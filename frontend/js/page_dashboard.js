var curve_display_timer = new Timer(20, display_new_curve)
var prices_history
var indexes
var is_krach
var default_prices
var dashboardRevision = -1
var lastKnownSaleId = 0

async function fetchMarketState(){
    const response = await fetch("/api/state", {cache: "no-store"})
    if(!response.ok){
        throw new Error("Could not load market state")
    }
    return response.json()
}

function applyMarketState(state, initialize = false){
    const previousIntervalCount = indexes ? indexes.party_index.length : 0
    default_prices = state.default_prices
    prices_history = state.prices.prices_history
    indexes = state.indexes
    is_krach = state.is_krach
    dashboardRevision = state.revision

    if(initialize){
        lastKnownSaleId = state.recent_sales.at(-1)?.id || 0
        init_chart()
        update_cheapest()
        generate_price_display()
    }else{
        for(const sale of state.recent_sales){
            if(sale.id > lastKnownSaleId){
                new_sale_animation(default_prices[sale.beer_code].colour, sale.price)
                lastKnownSaleId = sale.id
            }
        }

        if(indexes.party_index.length > previousIntervalCount){
            add_new_prices_to_chart()
            update_cheapest()
            update_prices_table()
        }
    }
    krach_style()
}

async function init(){
    applyMarketState(await fetchMarketState(), true)
    setInterval(() => curve_display_timer.check(), 1000)
    setInterval(async () => {
        try{
            const state = await fetchMarketState()
            if(state.revision !== dashboardRevision){
                applyMarketState(state)
            }
        }catch(error){
            console.error(error)
        }
    }, 1000)
}

init().catch(console.error)

function get_last_prices(index = -1){
    let last_prices = {}
    for(trigram in prices_history){
        last_prices[trigram] = prices_history[trigram].at(index)
    }

    return last_prices
}

function get_variation(){
    let variation = {}

    let last_prices = get_last_prices()
    let last_last_prices = get_last_prices(-2)
    for(trigram in prices_history){
        const previousPrice = last_last_prices[trigram] ?? last_prices[trigram]
        variation[trigram] = last_prices[trigram] / previousPrice
        variation[trigram] = round((variation[trigram] - 1) * 100, 2)
    }

    return variation
}

function update_cheapest(){
    let last_prices = get_last_prices()
	var cheapest = Object.keys(last_prices).map(function(key) {
        return [key, last_prices[key]];
    });

    cheapest.sort(function(first, second) {
        return first[1] - second[1];
    });
      
	cheapest = cheapest.splice(0,3)
	for(let i=0; i < 3; i++){
        let trigram = cheapest[i][0]
        document.querySelector("#cheapest .beer_name#rank_" + (i+1)).innerHTML = default_prices[trigram]["full_name"];
	}
}

function generate_price_display(){
    let last_prices = get_last_prices()
    let variation = get_variation()
    let price_table_body = document.querySelector('#price_table tbody');

	for(let trigram in default_prices){
        price_table_body.innerHTML +=
            "<tr class='price_" + trigram + "'>" +
				"<td style='color:" + default_prices[trigram]["colour"] + "'>&#11044;</td>" +
				"<td>" + default_prices[trigram]["full_name"] + "</td>" +
                "<td class='beer_code'>" + trigram + "</td>" +
                "<td class='price'>" + last_prices[trigram] + " kr.</td>" +
                "<td class='growth'>" + (variation[trigram] > 0 ? "+" : "") + variation[trigram] + "%</td>" +
			"</tr>"
        price_table_body.lastElementChild.setAttribute(
            "growth",
            variation[trigram] > 0 ? "positive" : variation[trigram] < 0 ? "negative" : "neutral"
        )
	}
}

function update_prices_table(){
    let last_prices = get_last_prices()
    let variation = get_variation()

	for(let trigram in default_prices){
        let beer_row = document.querySelector('#price_table .price_' + trigram);
        let price_cell = beer_row.querySelector('.price');
        let growth_cell = beer_row.querySelector('.growth');

        price_cell.innerText = last_prices[trigram] + " kr." 

        let variation_sign
        variation[trigram] > 0 ? variation_sign = "+" : variation_sign = ""
        growth_cell.innerText = variation_sign + variation[trigram] + "%"

        variation[trigram] > 0 ? variation_sign = "positive" : variation_sign = "neutral"
        variation[trigram] < 0 ? variation_sign = "negative" : ""
        beer_row.setAttribute("growth", variation_sign)
	}
}

function krach_style(){
    if(is_krach === true){
        document.querySelector("html").classList.add("active_krach")
    } else {
        document.querySelector("html").classList.remove("active_krach")
    }
}
