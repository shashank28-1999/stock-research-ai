import os
import streamlit as st

os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
os.environ["FINNHUB_API_KEY"] = st.secrets.get("FINNHUB_API_KEY", os.getenv("FINNHUB_API_KEY", ""))
os.environ["ALPHAVANTAGE_API_KEY"] = st.secrets.get("ALPHAVANTAGE_API_KEY", os.getenv("ALPHAVANTAGE_API_KEY", ""))

import pandas as pd
from utils.api_fetcher import get_all_data
from utils.financial_calculations import calculate_wacc, calculate_dcf, calculate_ratios
from utils.ai_analysis import generate_analysis
from utils.finnhub_fetcher import get_company_news, get_sentiment, get_earnings_surprise

st.set_page_config(
    page_title="AI Stock Research Assistant",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<style>
    .stApp, .main, .block-container { background-color: #ffffff !important; }
    h1, h2, h3, h4, h5, h6 { color: #1a1a1a !important; font-weight: 500 !important; }
    h1 { font-size: 2rem !important; font-weight: 600 !important; }
    .stTextInput input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #cccccc !important;
        border-radius: 6px !important;
    }
    .stTextInput input::placeholder { color: #999999 !important; }
    .stButton > button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
    }
    .stButton > button:hover { background-color: #333333 !important; }
    [data-testid="stMetric"] {
        background-color: #f9f9f9 !important;
        border: 1px solid #eeeeee !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    [data-testid="stMetricLabel"] { color: #666666 !important; }
    [data-testid="stMetricValue"] { color: #1a1a1a !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-bottom: 1px solid #eeeeee !important;
    }
    .stTabs [data-baseweb="tab"] { color: #666666 !important; }
    .stTabs [aria-selected="true"] { color: #1a1a1a !important; font-weight: 600 !important; }
    hr { border-color: #eeeeee !important; }
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("AI Stock Research")
st.caption("Fundamental analysis powered by Groq LLM + Alpha Vantage")
st.divider()

ticker = st.text_input(
    "Stock Ticker",
    placeholder="Enter a stock ticker",
    max_chars=10,
    label_visibility="collapsed"
)
analyze = st.button("Analyze", use_container_width=True)
st.caption("Example of tickers- US: AAPL · India: RELIANCE.NS · UK: HSBA.L · HK: 0700.HK · Korea: 005930.KS")

if analyze and ticker:
    with st.spinner(f"Fetching data for {ticker.upper()}..."):
        data, error = get_all_data(ticker)

    if error:
        st.error(f"{error}")
        st.stop()

    overview      = data["overview"]
    price_data    = data["price"]
    income        = data["income"]
    balance       = data["balance"]
    cashflow      = data["cashflow"]

    company_name  = overview.get("Name", ticker.upper())
    sector        = overview.get("Sector", "N/A")
    current_price = float(price_data.get("05. price", 0)) if price_data else 0
    change_pct    = price_data.get("10. change percent", "0%") if price_data else "0%"
    week_high     = overview.get("52WeekHigh", "N/A")
    week_low      = overview.get("52WeekLow", "N/A")

    st.markdown(f"### {company_name} ({ticker.upper()})")
    st.caption(sector)
    st.caption(f"Data source: {data.get('source', 'N/A')}")
    st.metric("Current Price", f"${current_price:,.2f}", change_pct)

    col1, col2 = st.columns(2)
    col1.metric("52W High", f"${week_high}")
    col2.metric("52W Low", f"${week_low}")
    st.divider()

    with st.spinner("Running financial calculations..."):
        wacc = calculate_wacc(overview, balance)
        dcf_value, free_cash_flow = calculate_dcf(cashflow, wacc)
        ratios = calculate_ratios(overview, balance, income, current_price)
        shares = ratios.get("shares_outstanding", 1)
        dcf_per_share = round(dcf_value / shares, 2) if dcf_value and shares else None
        upside = round(((dcf_per_share - current_price) / current_price) * 100, 2) if dcf_per_share and current_price else None

    with st.spinner("Generating AI analysis..."):
        analysis = generate_analysis(
            overview, ratios, wacc,
            dcf_value, free_cash_flow,
            income, balance
        )

    with st.spinner("Fetching latest news..."):
        news = get_company_news(ticker)
        sentiment = get_sentiment(ticker)
        earnings = get_earnings_surprise(ticker)

    tab1, tab2, tab3, tab4 = st.tabs(["Valuation", "Financials", "AI Analysis", "News & Sentiment"])

    with tab1:
        st.subheader("Valuation")
        st.metric("WACC", f"{round(wacc * 100, 2)}%")
        if dcf_per_share:
            st.metric("DCF Value Per Share", f"${dcf_per_share:,.2f}")
        else:
            st.metric("DCF Value Per Share", "N/A — Negative FCF")
        if upside is not None:
            delta_color = "normal" if upside > 0 else "inverse"
            st.metric("DCF Upside / Downside", f"{upside}%", delta=f"{upside}%", delta_color=delta_color)
        st.metric("Free Cash Flow", f"${free_cash_flow:,.0f}" if free_cash_flow else "N/A")
        st.divider()
        st.subheader("Ratios")
        col1, col2 = st.columns(2)
        col1.metric("P/E Ratio", ratios["pe_ratio"])
        col2.metric("Sector Avg P/E", ratios["sector_pe"])
        col3, col4 = st.columns(2)
        col3.metric("Debt to Equity", ratios["debt_to_equity"])
        col4.metric("Current Ratio", ratios["current_ratio"])
        st.metric("Return on Equity", f"{ratios['roe']}%")

    with tab2:
        st.subheader("Income Statement")
        if income:
            st.dataframe(pd.DataFrame({
                "Metric": ["Total Revenue", "Gross Profit", "Net Income", "EBITDA"],
                "Value ($)": [
                    f"${int(income.get('totalRevenue', 0)):,}",
                    f"${int(income.get('grossProfit', 0)):,}",
                    f"${int(income.get('netIncome', 0)):,}",
                    f"${int(income.get('ebitda', 0)):,}"
                ]
            }), use_container_width=True, hide_index=True)
        st.subheader("Balance Sheet")
        if balance:
            st.dataframe(pd.DataFrame({
                "Metric": ["Total Assets", "Total Liabilities", "Shareholder Equity", "Cash"],
                "Value ($)": [
                    f"${int(balance.get('totalAssets', 0)):,}",
                    f"${int(balance.get('totalLiabilities', 0)):,}",
                    f"${int(balance.get('totalShareholderEquity', 0)):,}",
                    f"${int(balance.get('cashAndCashEquivalentsAtCarryingValue', 0)):,}"
                ]
            }), use_container_width=True, hide_index=True)
        st.subheader("Cash Flow")
        if cashflow:
            st.dataframe(pd.DataFrame({
                "Metric": ["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"],
                "Value ($)": [
                    f"${int(cashflow.get('operatingCashflow', 0)):,}",
                    f"${int(cashflow.get('capitalExpenditures', 0)):,}",
                    f"${free_cash_flow:,.0f}" if free_cash_flow else "N/A"
                ]
            }), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Company Summary")
        st.info(analysis.get("company_summary", "N/A"))
        st.subheader("Valuation Explanation")
        st.write(analysis.get("valuation_explanation", "N/A"))
        st.subheader("Bull Case")
        st.success(analysis.get("bull_case", "N/A"))
        st.subheader("Bear Case")
        st.error(analysis.get("bear_case", "N/A"))
        st.subheader("Risk Factors")
        st.warning(analysis.get("risk_factors", "N/A"))

    with tab4:
        if sentiment:
            st.subheader("Market Sentiment")
            col1, col2, col3 = st.columns(3)
            col1.metric("Bullish", f"{sentiment['sentiment_score']}%")
            col2.metric("Bearish", f"{sentiment['bearish_percent']}%")
            col3.metric("Articles This Week", sentiment['articles_last_week'])
            st.divider()
        if earnings:
            st.subheader("Latest Earnings")
            col1, col2, col3 = st.columns(3)
            col1.metric("Period", earnings['period'])
            col2.metric("Actual EPS", earnings['actual'])
            col3.metric("Estimated EPS", earnings['estimate'])
            surprise = earnings['surprise_percent']
            delta_color = "normal" if surprise > 0 else "inverse"
            st.metric("Earnings Surprise", f"{surprise}%",
                      delta=f"{surprise}%", delta_color=delta_color)
            st.divider()
        if news:
            st.subheader("Latest News")
            for article in news:
                st.markdown(f"**{article.get('headline', 'No headline')}**")
                st.caption(f"{article.get('source', 'Unknown')} — {article.get('datetime', '')}")
                st.write(article.get('summary', ''))
                st.markdown(f"[Read more]({article.get('url', '#')})")
                st.divider()
        else:
            st.info("No recent news found.")

elif analyze and not ticker:
    st.warning("Please enter a ticker symbol.")

else:
    st.markdown("""
    ### How to use
    1. Enter any stock ticker — AAPL, MSFT, RELIANCE.NS, HSBA.L
    2. Tap Analyze
    3. Get instant AI-powered fundamental analysis
    Note: You must add exchange suffix for non-US stocks like .NS, .L, .HK

    **What you get**
    - DCF valuation with WACC
    - Full financials
    - AI bull case, bear case, risk factors
    """)