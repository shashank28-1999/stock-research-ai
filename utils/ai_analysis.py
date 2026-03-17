import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_analysis(overview, ratios, wacc, dcf_value, free_cash_flow, income, balance):
    company_name = overview.get("Name", "This company")
    sector = overview.get("Sector", "unknown sector")
    description = overview.get("Description", "")
    market_cap = overview.get("MarketCapitalization", "N/A")
    pe = ratios.get("pe_ratio", "N/A")
    sector_pe = ratios.get("sector_pe", "N/A")
    roe = ratios.get("roe", "N/A")
    de = ratios.get("debt_to_equity", "N/A")
    current_ratio = ratios.get("current_ratio", "N/A")
    revenue = income.get("totalRevenue", "N/A")
    net_income = income.get("netIncome", "N/A")
    total_assets = balance.get("totalAssets", "N/A")

    prompt = f"""
You are a senior equity research analyst. Analyze this company and provide structured insights.

COMPANY: {company_name}
SECTOR: {sector}
DESCRIPTION: {description[:500]}

FINANCIAL METRICS:
- Market Cap: {market_cap}
- P/E Ratio: {pe} (Sector Average: {sector_pe})
- Return on Equity: {roe}%
- Debt to Equity: {de}
- Current Ratio: {current_ratio}
- Revenue: {revenue}
- Net Income: {net_income}
- Total Assets: {total_assets}
- WACC: {round(wacc * 100, 2)}%
- DCF Intrinsic Value (total): ${dcf_value:,.0f} (based on Free Cash Flow of ${free_cash_flow:,.0f})

Provide exactly the following sections with these headers:

COMPANY_SUMMARY:
Write 2 sentences explaining what this company does for someone who has never heard of it.

VALUATION_EXPLANATION:
In 3 sentences explain what the DCF says, whether the stock appears overvalued or undervalued based on these metrics, and what the P/E vs sector average tells us.

BULL_CASE:
Give exactly 3 specific reasons to be optimistic about this stock based on the data.

BEAR_CASE:
Give exactly 3 specific reasons to be cautious about this stock based on the data.

RISK_FACTORS:
List exactly 3 key financial risk factors visible in this data.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    raw = response.choices[0].message.content
    return parse_analysis(raw)

def parse_analysis(raw_text):
    sections = {
        "company_summary": "",
        "valuation_explanation": "",
        "bull_case": "",
        "bear_case": "",
        "risk_factors": ""
    }
    markers = {
        "COMPANY_SUMMARY:": "company_summary",
        "VALUATION_EXPLANATION:": "valuation_explanation",
        "BULL_CASE:": "bull_case",
        "BEAR_CASE:": "bear_case",
        "RISK_FACTORS:": "risk_factors"
    }
    current_key = None
    for line in raw_text.split("\n"):
        stripped = line.strip()
        matched = False
        for marker, key in markers.items():
            if marker in stripped.upper():
                current_key = key
                remainder = stripped[stripped.upper().find(marker) + len(marker):].strip()
                if remainder:
                    sections[current_key] += remainder + "\n"
                matched = True
                break
        if not matched and current_key and stripped:
            sections[current_key] += line + "\n"
    for key in sections:
        sections[key] = sections[key].strip()
        if not sections[key]:
            sections[key] = "Analysis not available."
    return sections