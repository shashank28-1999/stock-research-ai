import requests
import os
import time
import yfinance as yf

ALPHA_VANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

def is_av_available():
    """Check if Alpha Vantage key exists and is not rate limited"""
    if not ALPHA_VANTAGE_KEY:
        return False
    try:
        params = {"function": "OVERVIEW", "symbol": "AAPL", "apikey": ALPHA_VANTAGE_KEY}
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if "Information" in data or "Note" in data:
            return False
        if "Symbol" in data:
            return True
        return False
    except:
        return False

# ── ALPHA VANTAGE FETCHERS ───────────────────────────────

def av_get_all_data(ticker):
    def fetch(function):
        params = {"function": function, "symbol": ticker, "apikey": ALPHA_VANTAGE_KEY}
        response = requests.get(BASE_URL, params=params)
        return response.json()

    overview_raw = fetch("OVERVIEW")
    if "Symbol" not in overview_raw:
        return None, "Alpha Vantage unavailable."
    time.sleep(1)

    price_raw = fetch("GLOBAL_QUOTE")
    price = price_raw.get("Global Quote", None)
    time.sleep(1)

    income_raw = fetch("INCOME_STATEMENT")
    income = income_raw.get("annualReports", [{}])[0]
    time.sleep(1)

    balance_raw = fetch("BALANCE_SHEET")
    balance = balance_raw.get("annualReports", [{}])[0]
    time.sleep(1)

    cashflow_raw = fetch("CASH_FLOW")
    cashflow = cashflow_raw.get("annualReports", [{}])[0]

    return {
        "overview": overview_raw,
        "price": price,
        "income": income,
        "balance": balance,
        "cashflow": cashflow,
        "source": "Alpha Vantage"
    }, None

# ── YFINANCE FETCHERS ────────────────────────────────────

def yf_get_all_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "symbol" not in info:
            return None, "Ticker not found."

        overview = {
            "Name": info.get("longName", ticker),
            "Sector": info.get("sector", "Other"),
            "Industry": info.get("industry", "N/A"),
            "Description": info.get("longBusinessSummary", ""),
            "MarketCapitalization": info.get("marketCap", "N/A"),
            "PERatio": info.get("trailingPE", 0),
            "Beta": info.get("beta", 1.0),
            "52WeekHigh": info.get("fiftyTwoWeekHigh", "N/A"),
            "52WeekLow": info.get("fiftyTwoWeekLow", "N/A"),
            "SharesOutstanding": info.get("sharesOutstanding", 1),
            "EPS": info.get("trailingEps", "N/A"),
        }

        price = {
            "05. price": str(info.get("currentPrice", info.get("regularMarketPrice", 0))),
            "10. change percent": str(round(info.get("regularMarketChangePercent", 0) * 100, 2)) + "%"
        }

        income = {
            "totalRevenue": info.get("totalRevenue", 0),
            "grossProfit": info.get("grossProfits", 0),
            "netIncome": info.get("netIncomeToCommon", 0),
            "ebitda": info.get("ebitda", 0),
        }

        balance = {
            "totalAssets": info.get("totalAssets", 0),
            "totalLiabilities": info.get("totalDebt", 0),
            "totalShareholderEquity": info.get("bookValue", 1) * info.get("sharesOutstanding", 1),
            "cashAndCashEquivalentsAtCarryingValue": info.get("totalCash", 0),
            "shortLongTermDebtTotal": info.get("totalDebt", 0),
            "totalCurrentAssets": info.get("totalCurrentAssets", 0),
            "totalCurrentLiabilities": info.get("totalCurrentLiabilities", 1),
        }

        cashflow = {
            "operatingCashflow": info.get("operatingCashflow", 0),
            "capitalExpenditures": info.get("capitalExpenditures", 0),
        }

        return {
            "overview": overview,
            "price": price,
            "income": income,
            "balance": balance,
            "cashflow": cashflow,
            "source": "yFinance"
        }, None

    except Exception as e:
        return None, f"Error fetching data: {str(e)}"

# ── MAIN ENTRY POINT ─────────────────────────────────────

def get_all_data(ticker):
    ticker = ticker.upper().strip()
    
    if ALPHA_VANTAGE_KEY:
        print("Trying Alpha Vantage...")
        data, error = av_get_all_data(ticker)
        if data:
            print("Using Alpha Vantage")
            return data, None
        print("Alpha Vantage failed, falling back to yFinance...")
    
    print("Using yFinance")
    return yf_get_all_data(ticker)