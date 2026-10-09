what_to_do_with_data = document.getElementById("what_to_do_with_data")
start_the_party = document.getElementById("start_the_party")
stock_market = document.getElementById("stock_market")
scheduler = document.getElementById("scheduler")
settings_panel = document.getElementById("settings_panel")

function tabs_to_display(){
    if(has_data()){
        what_to_do_with_data.style.display = "flex"
    } else {
        start_the_party.style.display = "flex"
    }
}
tabs_to_display()

function go_to_start(){
    start_the_party.style.display = "flex"
    start_the_party.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    })
}

function go_to_stock_market(){
    stock_market.style.display = "block"
    stock_market.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    })
    setTimeout(() => {
        what_to_do_with_data.style.display = "none"
        start_the_party.style.display = "none"
    }, 1000)
}

function go_to_scheduler(){
    scheduler.style.display = "flex"
    scheduler.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    })
}

function go_to_settings(){
    settings_panel.style.display = "flex"
    settings_panel.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    })
}

document.getElementById("resume").addEventListener("click", () => {
    go_to_stock_market()
    reload()
    init()
})

document.getElementById("download").addEventListener("click", () => {
    reload()
    download(sales.toCSV(), "sales.csv")
    download(prices.toCSV(), "prices.csv")
    download(indexes.toCSV(), "indexes.csv")
})

document.getElementById("reset").addEventListener("click", () => {
    go_to_start()
})

document.getElementById("schedule_start").addEventListener("click", () => {
    go_to_scheduler()
})

document.getElementById("start_now").addEventListener("click", () => {
    go_to_stock_market()
    start_from_nothing()
    open_dashboard()
})

document.getElementById("settings_button").addEventListener("click", () => {
    go_to_settings()
})

var countdown_til_start
document.getElementById("validate_schedule").addEventListener("click", () => {
    let extraction = extract_value_from_schedule()
    let datetime_start = extraction[0]
    let message = extraction[1]

    data_upload("countdown_end", datetime_start)
    data_upload("countdown_message", message)

    countdown_til_start = new Countdown(datetime_start, start_from_nothing)

    open_countdown()
    go_to_stock_market()

    interval_countdown_start = setInterval(() => {
        if(countdown_til_start.check()){
            clearInterval(interval_countdown_start)
        }
    }, (200));
})

function extract_value_from_schedule(){
    let date_start = document.querySelector("#schedule_start input[type=date]")
    let time_start = document.querySelector("#schedule_start input[type=time]")

    let datetime_start = date_start.value +"T"+ time_start.value +":00"

    if(datetime_start.length == 19){
        datetime_start = Date.parse(datetime_start)
    } else {
        datetime_start = ""
        throw 'start date field must be filled'
    }

    let message = document.querySelector("#schedule_message input").value

    return [datetime_start, message]
}

refresh_period_input = document.getElementById("refresh_period")
price_variation_amplification_input = document.getElementById("price_variation_amplification")
document.getElementById("validate_settings").addEventListener("click", () => {
    indexes.refresh_period = parseInt(refresh_period_input.value)
    prices.amplification = parseInt(price_variation_amplification_input.value)

    go_to_stock_market()
})

function open_countdown(){
    window.open('countdown.html')
}

function open_dashboard(){
    window.open('dashboard.html')
}
