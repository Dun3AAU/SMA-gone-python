<div align="center">
    <h1>Stock Market Anywhere</h1>
    <img src="frontend/images/SMA%20logo.png" style="max-width:500px"/>
    <h2>Developed by Marc Bresson</h2>
    <p align="center">
        <a href="https://linkedin.com/in/marc--bresson"><img src="https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555"/></a>
    </p>
</div>

Personal project: a market-style web app where prices vary with sales volume. The original version ran entirely in one browser; this repository now includes a Python-backed shared classroom version.

# Shared classroom version

The current multi-user version runs the existing frontend through a Python API. Students open the sale screen and public dashboard; the standalone legacy admin page is not served by the API, so its settings and krach controls are not exposed.

Install and start it from the repository root:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` on the host computer. Other students on the same network use `http://<host-computer-ip>:8000/`; the public display is at `/dashboard`. Allow inbound TCP port 8000 in the host firewall if needed.

`data/beers.json` is the active beer catalog. SQLite stores the shared sales ledger and price history in `data/market.sqlite3`. The server assigns each sale its price, uses idempotency keys for retries, and calculates new prices at 60-second intervals. Set `MARKET_DATABASE` to change the database path.

The default noise level is zero. To try local noise in PowerShell, set the value before starting the server; an explicit environment value overrides the database setting on startup:

```powershell
$env:MARKET_DATABASE = Join-Path $env:TEMP ("sma-gone-noise-" + [guid]::NewGuid().ToString() + ".sqlite3")
$env:MARKET_NOISE_PERCENT = "3"
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

This uses a fresh, isolated database in the Windows temp folder, leaving `data/market.sqlite3` untouched. Noise is a bounded random percentage added to the sales-driven price change each interval. `3` means up to 3 percentage points of random movement in either direction per interval. Close the server with Ctrl+C; use `Remove-Item Env:MARKET_NOISE_PERCENT, Env:MARKET_DATABASE` to unset these values in that PowerShell session. Omit `MARKET_NOISE_PERCENT` to preserve the noise value stored in the selected SQLite database.

Optional noise and simulated sales can also be configured through the token-protected `POST /api/admin/simulation` endpoint. Set `MARKET_ADMIN_TOKEN` before starting the server, then send it in the `X-Admin-Token` header with JSON fields `enabled`, `sales_per_minute`, `seed`, and `noise_percent`. The seed makes simulation/noise repeatable for a given sequence of intervals. The student page has no controls for those settings.

Run the backend tests with:

```powershell
python -m unittest backend.test_pricing backend.test_service -v
```

The previous standalone HTML workflow below is retained as historical documentation; use the Python launch instructions above for a shared market.

# Let the party begin !

![Countdown : let the party begin !](frontend/images/countdown.png)

You will need two screens for this app. One for the administration panel, where you register sales, and the other one for the public dashboard with prices, chart etc.

![administration panel](frontend/images/admin.png)

![administration interface](frontend/images/dashboard_normal_1.png)

## Initialisation

Edit your goods and prices in `parameters > default_prices.js`. You have to follow this structure :

```js
{
    "tgr" : { // the trigram of the good
        "full_name": "Trigram", // the full name of the good
        "initial_price": 1.0, // the start price
        "krach_price": 0.5, // the price of the good during the krach periods
        "min_price": 0.4 // OPTIONAL : the minimum price. If not specified, the good will not have any limit, and will be regulated by the market
    }
}
```

Open admin.html in Chrome or Edge (unfortunately, it doesn't work on Firefox, see #18), and follow the instructions. You will be prompted to either `Schedule the party`, or `Start now`.

![hello you](frontend/images/hello_you.png)

### Going with `Schedule the party`

![hello you](frontend/images/schedule_the_party.png)

You will be asked at what time to start the party, and for a message for the countdown. Once you click on `validate`, another window will pop-up with the displayed countdown. It is intended for the public. When the countdown hits 0, it will automatically switch to the dashboard.

### Going with `Start now`

This will immediately open the dashboard in another window. Place this window on your second public screen, and keep the admin panel for your team and yourself.

## During the party

### Make a sale

![Cart'naval](frontend/images/cartnaval.png)

By clicking on the buttons, you can register a new sale. You have a few information on every button :
- At the top in bold, you have the trigram followed by the full name
- At the bottom left in bold, you have the current price
- In green at the bottom, you have the variation between the initial price and the current price
- Just above the variation, you have the initial price
- In black on a colourful background, you have the number of sales during the current interval

### Make a krach

Using the light red button on the top right corner, you can immediatly start a krach period. During a krach, all prices drop down to what you defined in `default_prices.js`.

Prices after the krach will return to their pre-krach level.

![Dashboard krach](frontend/images/dashboard_krach.png)

### Change interval time or price variation amplification

If you want to change the default interval time (60s) or the default price variation amplification (100, see the wiki on how are new prices calculated), you can use the parameters button at the top of the administration panel.

Here, you can change parametres, and validate them by clicking the `validate` button.

![Parametres](frontend/images/parametres.png)

## Stop the party

There is no mecanism to stop the party. You can close the admin tab, or reload it. By doing so, the public dashboard will no longer be updated.

If you choose to reload it, you will be able to download your party data in CSV format.

![Download](frontend/images/party_going.png)

# License

This license lets you remix, adapt, and build upon this work non-commercially, as long as you credit me and license your new creations under the identical terms.

If you want to use it commercialy, do not hesitate to contact me, I will be glad to help.

![license CC BY-NC-SA](frontend/images/license.png)
