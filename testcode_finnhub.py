import finnhub
from datetime import datetime, timedelta, timezone
import random

# Initialize client
# Replace 'YOUR_API_KEY' with your actual Finnhub API Key
finnhub_client = finnhub.Client(api_key='d61nia1r01qgcobq661gd61nia1r01qgcobq6620')

def get_realtime_finance_news():
    # 1. Fetch general market news
    # Categories: 'general', 'forex', 'crypto', 'merger'
    news = finnhub_client.general_news('general', min_id=0)

    # save news as a json file
    import json
    with open('finnhub_news_response.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

    #print current time
    print(f"Current UTC Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Timestamp: {datetime.now(timezone.utc).timestamp()}")

    # 2. Define the 5-hour threshold
    # Finnhub timestamps are in Unix format (seconds)
    five_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=10)).timestamp()

    # 3. Filter for articles within the last 5 hours
    recent_news = [
        n for n in news 
        if n['datetime'] >= five_hours_ago
    ]

    if not recent_news:
        print("No articles found in the last 5 hours.")
        return

    # 4. Select 10 random articles (or all if fewer than 10)
    sample_size = min(len(recent_news), 100)
    random_selection = random.sample(recent_news, sample_size)

    print(f"--- 10 Random Real-Time Finance Articles (Last 5 Hours) ---\n")
    for i, article in enumerate(random_selection, 1):
        # Convert Unix timestamp to readable date
        date_str = datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{i}. {article['headline']}")
        print(f"   Source: {article['source']}")
        print(f"   Time: {date_str} UTC")
        print(f"   URL: {article['url']}\n")
        print(f"   Summary: {article['summary']}\n")

try:
    get_realtime_finance_news()
except finnhub.FinnhubAPIException as e:
    print(f"Finnhub API Exception: {e}")