import yfinance as yf
import pandas as pd

ticker = input("Please input your selected ticker: ")
stock= yf.Ticker(ticker)

# Statements data

income_statement = stock.income_stmt
income_statement = income_statement.iloc[:, :4]

balance_sheet = stock.balance_sheet
balance_sheet = balance_sheet.iloc[:, :4]

cash_flow = stock.cashflow
cash_flow = cash_flow.iloc[:, :4]

#print(income_statement.index)
#print(balance_sheet)
#print(cash_flow.index)

# Revenue and Revenue Growth

revenues = income_statement.loc["Total Revenue"].sort_index()
growth = revenues.pct_change().iloc[1:]
revenue_growth = growth.map(lambda x: f"{x:.2%}")
#print(revenues)
#print(revenue_growth)

# Operating Income and OPM

operating_income = income_statement.loc["Operating Income"].sort_index()
opm = operating_income / revenues
opm_percent = opm.map(lambda x: f"{x:.2%}")
#print(operating_income)
#print(opm_percent)

# Tax Rate

us_corporate_tax_rate = 0.21 # US Rate applied to all tickers. UK companies will be undertaxed by 4% if they pay main rate.
# Would use effective tax rate, but companies like AMD gave rates ranging from -70% to 19%.

# Depreciation and Amortization

d_and_a = cash_flow.loc["Depreciation And Amortization"].sort_index()
d_and_a_revenue = d_and_a / revenues
d_and_a_revenue_percent = d_and_a_revenue.map(lambda x: f"{x:.2%}")
#print(d_and_a)
#print(d_and_a_revenue_percent)

# CAPEX

capex = abs(cash_flow.loc["Capital Expenditure"].sort_index())
capex_revenue = capex / revenues
capex_revenue_percent = capex_revenue.map(lambda x: f"{x:.2%}")
#print(capex)
#print(capex_revenue_percent)

# Change in Working Capital

ciwc = cash_flow.loc["Change In Working Capital"].sort_index()
ciwc_revenues = ciwc / revenues
ciwc_percent = ciwc_revenues.map(lambda x: f"{x:.2%}")
#print(ciwc)
#print(ciwc_percent)

# Averages

revenue_growth_avg = growth.mean()

opm_average = opm.mean()

d_and_a_avg = d_and_a_revenue.mean()

capex_avg = capex_revenue.mean()

ciwc_avg = ciwc_revenues.mean()




#print( f"Rev growth: {revenue_growth_avg:.2%}")
#print(f"OPM: {opm_average:.2%}")
#print(f"D&A: {d_and_a_avg:.2%}")
#print(f"CAPEX: {capex_avg:.2%}")
#print(f"Change_WC {ciwc_avg:.2%}")


years = 5
last_revenue = revenues.iloc[-1]
rev_assumption = revenue_growth_avg
opm_assumption = opm_average
da_assumption = d_and_a_avg
capex_assumption = capex_avg
nwc_assumption = ciwc_avg


projected_ufcf = []
current = last_revenue

for year in range(years):
    prev_revenue = current
    current = current * (1 + rev_assumption)
    ebit = current * opm_assumption
    da_addback = current * da_assumption
    capex_outflow = current * capex_assumption
    nopat = ebit * (1 - us_corporate_tax_rate)
    delta_nwc = nwc_assumption * current
    ufcf = nopat + da_addback + delta_nwc - capex_outflow
    projected_ufcf.append(ufcf)

#print(projected_ufcf)

# Data for WACC

info = stock.info

raw_beta = info.get("beta") or 1.0
blume_beta = (0.67 * raw_beta ) + 0.33
market_cap = info.get("marketCap", 0)

ten_year_yield = yf.Ticker("^TNX").history(period="1d")["Close"].iloc[-1] / 100

spx = yf.Ticker("^SP500TR").history(period="20y")["Close"]
market_return = (spx.iloc[-1] / spx.iloc[0]) ** (1/20) - 1

total_debt = balance_sheet.loc["Total Debt"].sort_index().iloc[-1]

interest_expense = abs(income_statement.loc["Interest Expense"].sort_index().iloc[-1])

# WACC calc

cost_of_equity = ten_year_yield + blume_beta * (market_return - ten_year_yield)
cost_of_debt_pretax = interest_expense / total_debt
cost_of_debt_aftertax = cost_of_debt_pretax * (1 - us_corporate_tax_rate)
equity_weight = market_cap / (market_cap + total_debt)
debt_weight = total_debt / (market_cap + total_debt)
wacc = (cost_of_equity * equity_weight) + (cost_of_debt_aftertax * debt_weight)


# Terminal Value

perpetual_growth = 0.025
final_ufcf = projected_ufcf[-1]

assert perpetual_growth < wacc, "Growth rate must be below discount rate (WACC)"

terminal_value = final_ufcf * (1 + perpetual_growth) / (wacc - perpetual_growth)


discounted_ufcf = []
for t, ufcf in enumerate(projected_ufcf, start = 1):
    discount_factor = 1 / (1 + wacc) ** t
    discounted_ufcf.append(ufcf * discount_factor)

terminal_value_pv = terminal_value * (1 / (1 + wacc) ** years)

enterprise_value = sum(discounted_ufcf) + terminal_value_pv


cash_and_equivalents = balance_sheet.loc["Cash And Cash Equivalents"].sort_index().iloc[-1]
shares_outstanding = stock.info.get("sharesOutstanding")
equity_value = enterprise_value + cash_and_equivalents - total_debt

intrinsic_value_per_share = round(equity_value / shares_outstanding, 2)

print(intrinsic_value_per_share)













