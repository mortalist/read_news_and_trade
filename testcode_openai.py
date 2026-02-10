import openai
import requests
import os
import feedparser
import json
from collections import Counter



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
    You are a financial analyst analyzing the US MARKET. 
    Given the following news article, assign a sentiment score (-5(negative impact) to +5(positive impact)) 
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
    # print(response)
    return response.output_text

def decide_trades(scores):
    """Pick top 2 sectors to go long, bottom 1 to short."""
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    long_etfs = [SECTORS[sorted_scores[0][0]], SECTORS[sorted_scores[1][0]]]
    short_etf = SECTORS[sorted_scores[-1][0]]
    return long_etfs, short_etf

# Example usage
try:

    urls = [
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/economics/news.rss",
    "https://feeds.bloomberg.com/industries/news.rss",
    "https://feeds.bloomberg.com/business/news.rss",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", # CNBC Top News
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", # CNBC Finance
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001054", # CNBC Wealth
    "https://news.google.com/rss/search?q=finance&hl=en-US&gl=US&ceid=US%3Aen", # Google News Finance
    ]

    scorechart = {'Technology': 0, 
              'Semiconductors': 0, 
              'Financials': 0, 
              'Healthcare': 0, 
              'Energy': 0, 
              'Airlines': 0, 
              'Consumer Discretionary': 0, 
              'Consumer Staples': 0, 
              'Commodities': 0, 
              'Utilities': 0, 
              'Real Estate': 0}

    for url in urls:
        # Parse the feed
        feed = feedparser.parse(url)

        # Print feed title
        print(feed.feed.title)

        # Loop through entries
        for entry in feed.entries[:5]:  # limit to first 10
            print(entry.title)
            # print(entry.link)
            print(entry.published)
            # print entry.summary if it exists and is not empty 
            # if 'summary' in entry and entry.summary:
                # print(entry.summary)
            print()

            article_text = entry.title + "\n" + entry.published
            scores_json = analyze_article(article_text)
            scorechart = dict(Counter(scorechart) + Counter(json.loads(scores_json)))

    print("Sector Scores:", scorechart)


    longs, short = decide_trades(scorechart)
    print("Buy ETFs:", longs)
    print("Short ETF:", short)

except Exception as e:
    print("Error during analysis:", e)