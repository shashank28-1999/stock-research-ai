import requests
import os

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

def get_company_news(ticker):
    try:
        import datetime
        today = datetime.date.today()
        month_ago = today - datetime.timedelta(days=30)
        params = {
            "symbol": ticker,
            "from": str(month_ago),
            "to": str(today),
            "token": FINNHUB_KEY
        }
        response = requests.get(f"{BASE_URL}/company-news", params=params)
        news = response.json()
        if not isinstance(news, list):
            return []
        return news[:5]
    except:
        return []

def get_sentiment(ticker):
    try:
        params = {"symbol": ticker, "token": FINNHUB_KEY}
        response = requests.get(f"{BASE_URL}/news-sentiment", params=params)
        data = response.json()
        if "sentiment" not in data:
            return None
        return {
            "buzz_score": round(data.get("buzz", {}).get("buzz", 0), 2),
            "sentiment_score": round(data.get("sentiment", {}).get("bullishPercent", 0) * 100, 1),
            "bearish_percent": round(data.get("sentiment", {}).get("bearishPercent", 0) * 100, 1),
            "articles_last_week": data.get("buzz", {}).get("articlesInLastWeek", 0)
        }
    except:
        return None

def get_earnings_surprise(ticker):
    try:
        params = {"symbol": ticker, "token": FINNHUB_KEY}
        response = requests.get(f"{BASE_URL}/stock/earnings", params=params)
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        latest = data[0]
        return {
            "period": latest.get("period", "N/A"),
            "actual": latest.get("actual", "N/A"),
            "estimate": latest.get("estimate", "N/A"),
            "surprise_percent": round(latest.get("surprisePercent", 0), 2)
        }
    except:
        return None