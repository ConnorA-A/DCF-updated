DCF Valuation Model

This is a discounted cashflow model using Python that estimates the intrinsic value of a publicly listed non-financial company, using its historical financials pulled from Yahoo Finance.

The key idea behind this model is that Python does the heavy lifting of sourcing the financial data required. This model can run fully automatically once you input a ticker, but you usually shouldn't let it. 

The averages need human review first

You will be presented the companies 2022-2025 historicals, with a calculated average for:
- Revenue Growth
- Operating profit margin
- Depreciation and Amortization as a % of revenue
- Capex as % of revenue
- Change in working capital (%)
- Effective tax rate (presented only average)

Every input used in this DCF which requires judgement is overridable, because a company's future rarely looks like the average of its past.

This is what the model does:
- Pulls the income statement, balance sheet and cash flow statement of inputted ticker
- Derives historical drivers as said above
- Projects five years of unlevered free cash flow
- Calculates WACC (uses CAPM for cost of equity)
- Applies a Gordon-growth terminal value
- Bridges towards equity value and calculates intrinsic value per share
- Prints a 5x5 sensitivity table across WACC and terminal growth
- Displays every assumption used at the bottom, each of which are overrideable

How to run

1) pip install yfinance pandas numpy
2) python dcfmodelx2.py

The script prompts for a ticker then prints the historical drivers and their averages. It pauses at that point. Press Enter to run with the historical averages or CTRL-C to exit and set overrides. 
If you try it again after overriding the drivers and achieve a price where you're not happy about the beta or terminal growth rate given for example, you can override them as well and rerun the script.


Key features

The centre of this model is the override availability. Every driver defaults to its historical average but can be overridden

- revenue growth, OPM, capex as % of revenue and depreciation and amortization as % of revenue can be overridden with a full five year path (especially useful when you want to model a specific trajectory)
They can also be linearly interpolated between them for 5 years, after inputting a start and end value
(You choose one or the other per driver, not both)

- net change in working capital (%), effective tax rate, beta, terminal growth rate and equity risk premium can be overridden with a single value input. For effective tax rate and net change in working capital, this acts as an average.

The whole point of this is that no assumption is buried, each one is a visible deliberate decision.

Other key notes

- Beta uses Blume adjustment (0.67 * raw beta) + 0.33 by default, with an override for when you would rather set it from a sector reference
- Tax defaults to the effective tax rate (sum of historicals tax provision / sum of historicals pretax income), overridable when necessary
- ERP defaults to Damodaran's US equity risk permium, overrideable


Limitations

This model has two structural limitations, both worth stating clearly:

1. **The model is only as good as its assumptions.** Historical averages very often fail to capture a company's future trajectory, but seeing the historical data can help derive the potential trajectory.
   This is especially true for high growth or recently transformed firms, which can produce a significant undervaluation.
   The override panels exist precisely for this. Set explicit inputs when the averages don't match and feel free to try different inputs to evaluate different cases.

2. **Not valid for financial firms (banks, insurers, asset managers etc).** As debt is operational rather than a capital structure choice in financial firms, the enterprise-value / unlevered FCF framework breaks down.
   However, this is something I may revisit in the future.


One further note: the model is calibrated for US-listed companies. It uses the 10-year US treasury yield as the risk-free rate and US equity risk premium.
Non-US tickers will run, but the discount rate inputs won't be appropriate without adjustment


Build Story

I have always loved building DCF for firms on excel, but collecting the required financial data by hand was repetitive, so I set out to automate it. 
This wasn't my first attempt though, I originally tried pulling directly from SEC EDGAR filings but abandoned it because the tagging across companies was inconsistent. 

The archived attempt can be found here if you're interested: https://github.com/ConnorA-A/DCF_edgar_first_attempt

After that attempt I realised using yfinance would be much less of a headache


Validated on

So far I have validated the model on a few stocks including MSFT, TGT, KO, AMD, NFLX and they have worked smoothly.


