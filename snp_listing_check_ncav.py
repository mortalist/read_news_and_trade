import requests
import yfinance as yf
import pandas as pd
from analysis import f_score_analyzer, fs_score_analyzer
from io import StringIO

url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
headers = {"User-Agent": "Mozilla/5.0"}

# 1. Fetch the data
response = requests.get(url, headers=headers)

# 2. Use StringIO to wrap the raw text (this prevents the "raw html" issue)
html_data = StringIO(response.text)

# 3. Read the table
# The [0] is crucial because read_html always returns a LIST of tables
df = pd.read_html(html_data)[0]

# 4. Display the result
print(df[['Symbol', 'Security']])

skipping_tickers = []  # List to keep track of tickers that are skipped due to errors
ncav_axis = []  # List to store NCAV ratios for potential NCAV stocks
return_axis = []  # List to store returns for potential NCAV stocks

for ticker in df['Symbol'].tolist():
    # print(f"\nAnalyzing {ticker}...")
    analTicker = yf.Ticker(ticker)
    balance_sheet = analTicker.balance_sheet
    # print(balance_sheet)
    #list all the columns in balance_sheet
    # print(balance_sheet.index)

    #continue loop if 'Current Assets' or 'Total Liabilities Net Minority Interest' is not in the balance sheet
    if 'Current Assets' not in balance_sheet.index or 'Total Liabilities Net Minority Interest' not in balance_sheet.index:
        # print(f"Warning: Missing 'Current Assets' or 'Total Liabilities Net Minority Interest' for {ticker}, skipping...")
        skipping_tickers.append(ticker)
        continue

    current_assets = balance_sheet.loc['Current Assets'].iloc[0]
    # print(f"current Assets for {ticker}: {current_assets}")

    total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]
    # print(f"Total Liabilities for {ticker}: {total_liabilities}")

    ncav_ratio = (current_assets - total_liabilities) / current_assets if current_assets != 0 else 0
    # print(f"NCAV STRAT CHECK for {ticker}: {ncav_ratio:.2%}")
    if ncav_ratio != 0:  # Example threshold for NCAV strategy

        hist = analTicker.history(period="2mo", interval="1d")
            
            # Validate data before processing
        if hist.empty or len(hist) < 2:
                print(f"Warning: Not enough data for {ticker}, skipping...")
                skipping_tickers.append(ticker)
                continue
            
        if 'Open' not in hist.columns:
                print(f"Warning: No 'Open' data for {ticker}, skipping...")
                skipping_tickers.append(ticker)
                continue
        return_pct = ((hist['Open'].iloc[-1]) / (hist['Open'].iloc[0]) - 1) * 100

        print(f"{ticker} is a potential NCAV stock with a ratio of {ncav_ratio:.2%} and a return of {return_pct:.2f}% for the 2mo period.")
        ncav_axis.append(ncav_ratio)
        return_axis.append(return_pct)

print(f"\nTickers skipped due to missing data: {', '.join(skipping_tickers)}")

import matplotlib.pyplot as plt
plt.scatter(ncav_axis, return_axis)
plt.title('NCAV Ratio vs Return for Potential NCAV Stocks')
plt.xlabel('NCAV Ratio')
plt.ylabel('Return (%)')
plt.grid()
plt.show()