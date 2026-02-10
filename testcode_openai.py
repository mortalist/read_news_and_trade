import openai
import requests
import os

# Set your API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define sectors and ETF mapping
SECTORS = {
    "Technology": "XLK",
    "Semiconductors": "SMH",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Airlines": "JETS",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Commodities": "DBC",
    "Utilities": "XLU",
    "Real Estate": "XLRE"
}

def analyze_article(article_text):
    """Send article text to ChatGPT and get sector sentiment scores."""
    prompt = f"""
    You are a financial analyst. 
    Given the following news article, assign a sentiment score (-5 to +5) 
    for each sector below based on how the article might impact it:

    Sectors: {list(SECTORS.keys())}

    Article:
    {article_text}

    Return output as JSON with sector names as keys and scores as values.
    """

    response = openai.responses.create(
        model="gpt-5-nano",
        instructions="you are a helpful assistant that analyzes financial news articles.",
        input = prompt
    )
    print(response)
    return response.output_text

def decide_trades(scores):
    """Pick top 2 sectors to go long, bottom 1 to short."""
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    long_etfs = [SECTORS[sorted_scores[0][0]], SECTORS[sorted_scores[1][0]]]
    short_etf = SECTORS[sorted_scores[-1][0]]
    return long_etfs, short_etf

# Example usage
if __name__ == "__main__":
    # Replace with your scraped article text
    article_text = "NVIDIA reports record earnings due to AI chip demand..."
    
    scores_json = analyze_article(article_text)
    print("Sector Scores:", scores_json)

    # Convert JSON string to dict
    import json
    scores = json.loads(scores_json)

    longs, short = decide_trades(scores)
    print("Buy ETFs:", longs)
    print("Short ETF:", short)