"""
DCF model to calculate intrinsic value of given stock ticker. This model pulls financial data via yfinance library, projects 5yr 
unlevered FCF with full assumption-overrides available, discounts at WACC and includes a sensitivity table against WACC x terminal growth.

TWO main limitations
1. The model is only as good as its assumptions. Historical averages often fail to capture future growth trajectory, especially for high growth firms,
producing a significantly undervalued result. Use the override panels to set explicit inputs when the averages don't reflect a companies current business model.
2. The model is not valid for financial firms e.g. banking, insurance, asset management etc. As debt is operational rather than a capital structure choice, the
enterprise value / unlevered FCF framework breaks down. However, this is something I may look into at a future date.
"""


import yfinance as yf
import pandas as pd
import numpy as np

ticker = input("Please input your selected ticker: ")
stock = yf.Ticker(ticker)

# Statements data

income_statement = stock.income_stmt
income_statement = income_statement.iloc[:, :4]

balance_sheet = stock.balance_sheet
balance_sheet = balance_sheet.iloc[:, :4]

cash_flow = stock.cashflow
cash_flow = cash_flow.iloc[:, :4]

# Override controls for full list

growth_path_override = None
opm_path_override = None
da_path_override = None
capex_path_override = None

# Override controls for start/end (you can't override the same assumption with both the list and start/end. Only choose the most appropriate one)

start_override_g = None
end_override_g = None
opm_override_start = None
opm_override_end = None
da_override_start = None
da_override_end = None
capex_override_start = None
capex_override_end = None
nwc_override = None
tax_rate_override =None
beta_override = None
terminal_g_override = None
erp_override = None

# Revenue and Revenue Growth

revenues = income_statement.loc["Total Revenue"].sort_index()
growth = revenues.pct_change().iloc[1:]
revenue_growth = growth.map(lambda x: f"{x:.2%}")

# Operating Income and OPM

operating_income = income_statement.loc["Operating Income"].sort_index()
opm = operating_income / revenues
opm_percent = opm.map(lambda x: f"{x:.2%}")

# Tax Rate

tax_provision = income_statement.loc["Tax Provision"].sort_index()
pretax_income = income_statement.loc["Pretax Income"].sort_index()
effective_tax_rate = tax_provision.sum() / pretax_income.sum() 
tax_rate = tax_rate_override if tax_rate_override is not None else effective_tax_rate

# Depreciation and Amortization

d_and_a = cash_flow.loc["Depreciation Amortization Depletion"].sort_index()
d_and_a_revenue = d_and_a / revenues
d_and_a_revenue_percent = d_and_a_revenue.map(lambda x: f"{x:.2%}")

# CAPEX

capex = abs(cash_flow.loc["Capital Expenditure"].sort_index())
capex_revenue = capex / revenues
capex_revenue_percent = capex_revenue.map(lambda x: f"{x:.2%}")

# Change in Working Capital

ciwc = cash_flow.loc["Change In Working Capital"].sort_index()
ciwc_revenues = ciwc / revenues
ciwc_percent = ciwc_revenues.map(lambda x: f"{x:.2%}")

# Averages

revenue_growth_avg = growth.mean()

opm_average = opm.mean()

d_and_a_avg = d_and_a_revenue.mean()

capex_avg = capex_revenue.mean()

ciwc_avg = ciwc_revenues.mean()

# Summary DF

summary = pd.DataFrame({
    "Revenue Growth": growth,
    "OPM": opm,
    "D&A %": d_and_a_revenue,
    "CAPEX %": capex_revenue,
    "Change in WC %": ciwc_revenues
})
summary.index = summary.index.year
summary.loc["Average"] = summary.mean()

# Revenue growth for 2022 will be empty as data for 2021 wasn't available

print(f"\nHistoricals and Average")
print()
print(summary.T.map(lambda x: f"{x:.2%}" if pd.notna(x) else "-"))
print(f"Effective Tax Rate: {effective_tax_rate:.2%}")

try:
    input(f"\nReview the averages which will be used in the model before continuing. If you want to override anything press CTRL-C and refer to the override controls. If you're happy with the averages, press enter")
except KeyboardInterrupt:
    print("Sucessfully exited")
    raise SystemExit



years = 5
last_revenue = revenues.iloc[-1]
nwc_assumption = nwc_override if nwc_override is not None else ciwc_avg

# Revenue path

default_terminal_g = 0.025
terminal_g = terminal_g_override if terminal_g_override is not None else default_terminal_g


if growth_path_override is not None:
    assert len(growth_path_override) == years, "Growth path must have exactly 5 values"
    growth_path = np.array(growth_path_override)
else:
    start_g = start_override_g if start_override_g is not None else growth.iloc[-1]
    end_g = end_override_g if end_override_g is not None else terminal_g
    growth_path = np.linspace(start_g, end_g, years)


revenue_path = []
current = last_revenue

for year in range(years):
    current = current * (1 + growth_path[year])
    revenue_path.append(current)


# OPM path

if opm_path_override is not None:
    assert len(opm_path_override) == years, "OPM path must have exactly 5 values"
    opm_path = np.array(opm_path_override)
else:
    opm_start = opm_override_start if opm_override_start is not None else opm_average
    opm_end = opm_override_end if opm_override_end is not None else opm_average
    opm_path = np.linspace(opm_start, opm_end, years)

# Depreciation and Amortization path

if da_path_override is not None:
    assert len(da_path_override) == years, "D&A path must have exactly 5 values"
    da_path = np.array(da_path_override)
else:
    da_start = da_override_start if da_override_start is not None else d_and_a_avg
    da_end = da_override_end if da_override_end is not None else d_and_a_avg
    da_path = np.linspace(da_start, da_end, years)

# Capex path

if capex_path_override is not None:
    assert len(capex_path_override) == years, "CAPEX path must have exactly 5 values"
    capex_path = np.array(capex_path_override)
else:
    capex_start = capex_override_start if capex_override_start is not None else capex_avg
    capex_end = capex_override_end if capex_override_end is not None else capex_avg
    capex_path = np.linspace(capex_start, capex_end, years)

# Assumptions used

assumptions = pd.DataFrame({
    "Revenue Growth": growth_path,
    "OPM": opm_path,
    "D&A %": da_path,
    "CAPEX %": capex_path,
}, index = [f"Year {i+1}" for i in range(years)])

projected_ufcf = []


for year in range(years):
    current = revenue_path[year]
    ebit = current * opm_path[year]
    da_addback = current * da_path[year]
    capex_outflow = current * capex_path[year]
    nopat = ebit * (1 - tax_rate)
    delta_nwc = nwc_assumption * current
    ufcf = nopat + da_addback + delta_nwc - capex_outflow
    projected_ufcf.append(ufcf)


# Data for WACC

info = stock.info

raw_beta = info.get("beta") or 1.0
blume_beta = (0.67 * raw_beta ) + 0.33
beta = beta_override if beta_override is not None else blume_beta

market_cap = info.get("marketCap", 0)

ten_year_yield = yf.Ticker("^TNX").history(period="1d")["Close"].iloc[-1] / 100


default_erp = 0.0445 # Damodarans equity risk premium for united states July 2026
equity_risk_premium = erp_override if erp_override is not None else default_erp

total_debt = balance_sheet.loc["Total Debt"].sort_index().iloc[-1]

interest_expense = abs(income_statement.loc["Interest Expense"].sort_index().iloc[-1])

cash_and_equivalents = balance_sheet.loc["Cash Cash Equivalents And Short Term Investments"].sort_index().iloc[-1]
shares_outstanding = stock.info.get("sharesOutstanding")


# WACC calc

cost_of_equity = ten_year_yield + beta * equity_risk_premium
cost_of_debt_pretax = interest_expense / total_debt
cost_of_debt_aftertax = cost_of_debt_pretax * (1 - tax_rate)
equity_weight = market_cap / (market_cap + total_debt)
debt_weight = total_debt / (market_cap + total_debt)
wacc = (cost_of_equity * equity_weight) + (cost_of_debt_aftertax * debt_weight)


# Terminal Value

def price_at(wacc, terminal_g):
    if terminal_g >= wacc:
        return np.nan

    final_ufcf = projected_ufcf[-1]
    terminal_value = final_ufcf * (1 + terminal_g) / (wacc - terminal_g)

    discounted_ufcf = []
    for t, ufcf in enumerate(projected_ufcf, start = 1):
        discount_factor = 1 / (1 + wacc) ** t
        discounted_ufcf.append(ufcf * discount_factor)

    terminal_value_pv = terminal_value * (1 / (1 + wacc) ** years)
    enterprise_value = sum(discounted_ufcf) + terminal_value_pv

    equity_value = enterprise_value + cash_and_equivalents - total_debt
    return round((equity_value / shares_outstanding), 2)



print(f"\nThe Intrinsic value per share of {ticker.upper()} is  ${price_at(wacc, terminal_g)}")

# Sensitivity Table

wacc_steps = np.array([-0.01, -0.005, 0, 0.005, 0.01])
tg_steps = np.array([-0.005, -0.0025, 0, 0.0025, 0.005])

wacc_axis = wacc + wacc_steps
terminal_g_axis = terminal_g + tg_steps

table = []
for w in wacc_axis: 
    row = []
    for tg in terminal_g_axis:
        row.append(price_at(w, tg))
    table.append(row)

sensitivity_table = pd.DataFrame(table, index = (wacc_axis * 100).round(2), columns = (terminal_g_axis * 100).round(2))
sensitivity_table.index.name = 'WACC (%)'
sensitivity_table.columns.name = 'terminal growth (%)'
formatted_sensitivity = sensitivity_table.map(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
print(f"\nSensitivity Table")
print(f"\n{formatted_sensitivity}")

# Assumptions used in projection print

print("\nAssumptions used in this projection")
print()
print(assumptions.T.map(lambda x: f"{x:.2%}"))
print(f"\nChange in WC %: {nwc_assumption:.2%}")
print(f"Beta used: {round(beta, 2)}")
print(f"WACC used: {wacc:.2%}")
print(f"Terminal Growth Rate: {terminal_g:.2%}")
print(f"Tax Rate: {tax_rate:.2%}")
print(f"Equity Risk Premium: {equity_risk_premium:.2%}")














