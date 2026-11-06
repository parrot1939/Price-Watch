# PriceWatch

A Python command-line application for tracking product prices from publicly accessible HTML pages. PriceWatch stores historical price observations in SQLite, detects when a target price is reached, calculates price statistics, and exports historical data to CSV.

**Project type:** Python portfolio project · Web scraping · Relational database · Data analysis · Automated tests

## Features

- Register products with a name, URL, CSS price selector, currency and optional target price.
- Fetch prices using Requests and parse HTML with Beautiful Soup.
- Support common European and US price formats, such as `2 499,99 zł` and `$1,299.99`.
- Persist products and timestamped price observations with SQLAlchemy and SQLite.
- Check one product or all registered products with a configurable delay between requests.
- Print a target-price alert in the terminal when a product reaches or falls below its threshold.
- View price history and calculate minimum, maximum, average, latest price and overall change using pandas.
- Export observations to CSV.
- Run offline automated tests with pytest and local HTML fixtures.

**Important:** This project does **not** send emails or notifications, run scheduled checks, render JavaScript, or support every e-commerce website. A target alert is printed during a manual `check` command. Some sites block scraping or render prices dynamically.

## Tech stack

| Technology | Purpose |
| --- | --- |
| Python 3.11+ | Application logic and CLI |
| Requests | HTTP requests |
| Beautiful Soup | HTML parsing and CSS selectors |
| SQLAlchemy 2 | ORM and persistence |
| SQLite | Local database |
| pandas | History tables, statistics and CSV export |
| argparse | Command-line interface |
| pytest | Automated tests |

## Project structure

```text
pricewatch/
├── app/
│   ├── __init__.py
│   ├── analytics.py       # Historical data and statistics
│   ├── cli.py             # CLI commands and error handling
│   ├── database.py        # Database engine and sessions
│   ├── models.py          # Product and PriceObservation tables
│   ├── scraper.py         # HTTP, HTML parsing, price normalization
│   └── services.py        # Product and observation business logic
├── tests/
│   ├── conftest.py        # Isolated test database
│   ├── fixtures/
│   │   └── product.html   # Local sample HTML
│   ├── test_scraper.py
│   └── test_services.py
├── main.py                # Entry point
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation (Windows PowerShell)

Open PowerShell in the extracted `pricewatch` directory (the one containing `main.py` and `requirements.txt`).

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation scripts, run this **in the current PowerShell window** and then retry activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternatively, you can skip activation and replace `python` in the commands below with `.\.venv\Scripts\python.exe`.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Quick start

PriceWatch works with ordinary, publicly accessible HTML where a price is present in the server response. **The URL below is an illustrative placeholder, not a real product page**. Replace it with a page you have permission to fetch and adjust the CSS selector to match its price element.

```powershell
python main.py add --name "Demo Laptop" --url "https://example.com/product" --selector ".product-price" --target 2500 --currency PLN
python main.py list
python main.py check --id 1
python main.py history 1
python main.py stats 1
python main.py history 1 --csv prices.csv
python main.py remove 1
```

The example `check` command will fail until you provide a **real URL and matching CSS selector**. This is expected. For a fully offline demonstration, run `python -m pytest -v`; the test suite includes a sample HTML product page.

### How to find a CSS selector

1. Open a permitted product page in your browser.
2. Right-click the displayed price and select **Inspect**.
3. Identify a stable element class or ID, such as `<span class="product-price">`.
4. Use `.product-price` as the selector (or `#price` for an ID).
5. Check that the price is included in the page's original HTML; JavaScript-only prices are not supported.

### Command reference

| Command | Description |
| --- | --- |
| `python main.py add --name NAME --url URL --selector CSS [--target AMOUNT] [--currency PLN]` | Register a product |
| `python main.py list` | List products with latest recorded prices |
| `python main.py check [--id ID] [--delay SECONDS]` | Check one or all products; default delay is 2 seconds |
| `python main.py history ID [--csv FILE]` | Display and optionally export history |
| `python main.py stats ID` | Display descriptive price statistics |
| `python main.py remove ID` | Remove a product and its observations |
| `python main.py --help` | Display help |

The `--db` option may be placed **before** the subcommand to use another SQLAlchemy database URL, e.g. `python main.py --db sqlite:///demo.db list`. By default, the database file `pricewatch.db` is created in the project directory. You may also set the `PRICEWATCH_DB_URL` environment variable.

## Database schema

### `products`

| Field | Description |
| --- | --- |
| `id` | Primary key |
| `name` | Product display name |
| `url` | Unique product URL |
| `selector` | CSS selector for the price element |
| `currency` | Three-letter currency code (display only) |
| `target_price` | Optional alert threshold |
| `created_at` | Creation timestamp |

### `price_observations`

| Field | Description |
| --- | --- |
| `id` | Primary key |
| `product_id` | Foreign key to `products` |
| `price` | Decimal price value |
| `checked_at` | Observation timestamp |

One product can have many observations. Removing a product through the ORM also deletes its recorded observations.

## Testing

Run all tests from the project root:

```powershell
python -m pytest -v
```

The tests use temporary SQLite databases and a local HTML fixture. They do not make live HTTP requests, so they can run without an internet connection.

## Architecture

- `scraper.py` validates HTTP(S) URLs, requests HTML, selects the price element and normalizes price strings into `Decimal` values.
- `models.py` defines the SQLAlchemy entities and the one-to-many relationship between products and price observations.
- `services.py` handles product registration, database queries, recording prices and threshold comparisons.
- `analytics.py` converts stored observations into pandas DataFrames and calculates summary statistics.
- `cli.py` exposes commands, formats output and reports errors without crashing the entire batch when one page fails.

## Limitations and responsible use

- Only scrape websites when permitted by their terms and `robots.txt`; avoid excessive request rates. A delay is applied between requests when checking multiple products.
- This application does not bypass CAPTCHAs, authentication or anti-bot protections.
- CSS selectors vary by website and may change over time.
- JavaScript-rendered prices are not supported by the Requests-based scraper.
- Price strings may contain ambiguous number formatting; verify parsed values before relying on them.
- Currency codes are labels only; no currency conversion is performed.
- The program is intended for local, trusted use. Do not expose it as a public scraping service without additional safeguards against unsafe URLs and network access.

## Potential improvements

- A scheduler for periodic checks.
- Email or desktop notifications.
- A web dashboard and price history charts.
- Pluggable parsers for supported stores.
- More extensive currency/locale support.
- Database migrations and structured JSON logging.

## License

This repository does not include a license by default. Add a license file if you wish to define reuse permissions.
