bias_dict = {
        "Technology": 1.2,
        "Semiconductors": 2,
        "Financials": 3,
        "Healthcare": 4,
        "Energy": 5,
        "Airlines": 6.6,
        "Consumer Discretionary": 7,
        "Consumer Staples": 8,
        "Commodities": 9,
        "Utilities": 10,
        "Real Estate": 11
    }

score_dict = {
        "Technology": 1,
        "Semiconductors": 2,
        "Financials": 3,
        "Healthcare": 4,
        "Energy": 5,
        "Airlines": 6,
        "Consumer Discretionary": 7,
        "Consumer Staples": 8,
        "Commodities": 9,
        "Utilities": 10,
        "Real Estate": 11
    }

for sector in bias_dict:
    score_dict[sector] *= bias_dict[sector]

for sector, score in score_dict.items():
    print(f"{sector}: {score}")