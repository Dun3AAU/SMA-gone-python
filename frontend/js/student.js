const studentDrinks = document.getElementById("drinks")
const studentButtons = {}
const pendingSales = new Set()
let latestSaleId = 0
let hasLoadedInitialSales = false
let refreshingMarket = false

async function getMarketState(){
    const response = await fetch("/api/state", {cache: "no-store"})
    if(!response.ok){
        throw new Error("Could not load market state")
    }
    return response.json()
}

async function refreshStudentMarket(){
    if(refreshingMarket){
        return
    }
    refreshingMarket = true
    try{
    const state = await getMarketState()
    const codes = Object.keys(state.default_prices)

    for(const code of codes){
        if(!studentButtons[code]){
            const beer = state.default_prices[code]
            const button = new SaleButton(code, beer.full_name, beer.initial_price, beer.colour)
            studentButtons[code] = button
            studentDrinks.appendChild(button.html())
            button.dom.addEventListener("click", () => submitBeerSale(code))
        }

        const button = studentButtons[code]
        const currentPrice = state.current_prices[code]
        if(button.actual_price !== currentPrice){
            button.update_dom(currentPrice)
        }
        button.number_of_sales = state.active_sales[code] || 0
        button.update_counter()
        if(!pendingSales.has(code)){
            button.dom.removeAttribute("disabled")
        }
    }

    document.getElementById("remaining_time_til_new_prices").innerText = state.time_until_next

    if(!hasLoadedInitialSales){
        latestSaleId = state.recent_sales.at(-1)?.id || 0
        hasLoadedInitialSales = true
    }else{
        for(const sale of state.recent_sales){
            if(sale.id > latestSaleId){
                new_sale_animation(state.default_prices[sale.beer_code].colour, sale.price)
                latestSaleId = sale.id
            }
        }
    }
    marketError.hidden = true
    }finally{
        refreshingMarket = false
    }
}

async function submitBeerSale(code){
    const button = studentButtons[code]
    if(button.dom.hasAttribute("disabled")){
        return
    }

    pendingSales.add(code)
    button.dom.setAttribute("disabled", "")
    try{
        const response = await fetch("/api/sales", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({beer_code: code, request_id: makeRequestId()})
        })
        if(!response.ok){
            throw new Error("Sale was rejected")
        }
        const sale = await response.json()
        new_sale_animation(button.colour, sale.price)
        latestSaleId = Math.max(latestSaleId, sale.id)
        await refreshStudentMarket()
    }catch(error){
        console.error(error)
        document.getElementById("market_error").hidden = false
    }finally{
        pendingSales.delete(code)
        if(!refreshingMarket){
            button.dom.removeAttribute("disabled")
        }
    }
}

function makeRequestId(){
    if(crypto.randomUUID){
        return crypto.randomUUID()
    }
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

const marketError = document.createElement("div")
marketError.id = "market_error"
marketError.setAttribute("role", "alert")
marketError.hidden = true
marketError.innerText = "Connection interrupted. Please try again."
document.getElementById("student_market").prepend(marketError)

refreshStudentMarket().catch((error) => {
    console.error(error)
    marketError.hidden = false
})
setInterval(() => refreshStudentMarket().catch(console.error), 1000)