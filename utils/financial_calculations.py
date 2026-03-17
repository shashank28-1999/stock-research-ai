SECTOR_PE_AVERAGES = {
    "Technology": 28.0,
    "Financial Services": 14.0,
    "Healthcare": 22.0,
    "Consumer Cyclical": 18.0,
    "Consumer Defensive": 20.0,
    "Energy": 12.0,
    "Industrials": 17.0,
    "Real Estate": 35.0,
    "Utilities": 16.0,
    "Materials": 15.0,
    "Communication Services": 20.0,
    "Other": 18.0
}

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def calculate_wacc(overview, balance):
    beta = safe_float(overview.get("Beta"), 1.0)
    risk_free_rate = 0.045
    equity_risk_premium = 0.055
    cost_of_equity = risk_free_rate + beta * equity_risk_premium
    total_equity = safe_float(balance.get("totalShareholderEquity"), 1)
    total_debt = safe_float(balance.get("shortLongTermDebtTotal"), 0)
    total_capital = total_equity + total_debt
    if total_capital == 0:
        return cost_of_equity
    equity_weight = total_equity / total_capital
    debt_weight = total_debt / total_capital
    cost_of_debt = 0.05
    tax_rate = 0.21
    wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
    return round(wacc, 4)

def calculate_dcf(cashflow, wacc):
    free_cash_flow = safe_float(cashflow.get("operatingCashflow"), 0) - safe_float(cashflow.get("capitalExpenditures"), 0)
    if free_cash_flow <= 0:
        return None, free_cash_flow
    growth_rate = 0.08
    terminal_growth = 0.03
    projected_fcf = []
    for year in range(1, 6):
        fcf = free_cash_flow * ((1 + growth_rate) ** year)
        discounted = fcf / ((1 + wacc) ** year)
        projected_fcf.append(discounted)
    terminal_value = (projected_fcf[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
    discounted_terminal = terminal_value / ((1 + wacc) ** 5)
    dcf_value = sum(projected_fcf) + discounted_terminal
    return round(dcf_value, 2), round(free_cash_flow, 2)

def calculate_ratios(overview, balance, income, current_price):
    pe_ratio = safe_float(overview.get("PERatio"), 0)
    sector = overview.get("Sector", "Other")
    sector_pe = SECTOR_PE_AVERAGES.get(sector, 18.0)
    total_debt = safe_float(balance.get("shortLongTermDebtTotal"), 0)
    total_equity = safe_float(balance.get("totalShareholderEquity"), 1)
    debt_to_equity = round(total_debt / total_equity, 2) if total_equity else 0
    current_assets = safe_float(balance.get("totalCurrentAssets"), 0)
    current_liabilities = safe_float(balance.get("totalCurrentLiabilities"), 1)
    current_ratio = round(current_assets / current_liabilities, 2) if current_liabilities else 0
    net_income = safe_float(income.get("netIncome"), 0)
    roe = round((net_income / total_equity) * 100, 2) if total_equity else 0
    shares_outstanding = safe_float(overview.get("SharesOutstanding"), 1)
    return {
        "pe_ratio": pe_ratio,
        "sector_pe": sector_pe,
        "sector": sector,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "roe": roe,
        "shares_outstanding": shares_outstanding
    }