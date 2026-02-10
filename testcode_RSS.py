import feedparser

# Example RSS feed (BBC News)
# url = "http://feeds.bbci.co.uk/news/rss.xml"
# url = "https://feeds.bloomberg.com/markets/news.rss"
# url = "https://feeds.bloomberg.com/economics/news.rss"
# url = "https://feeds.bloomberg.com/industries/news.rss"
# url = "https://feeds.bloomberg.com/business/news.rss"

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

for url in urls:
    # Parse the feed
    feed = feedparser.parse(url)

    # Print feed title
    print(feed.feed.title)

    # Loop through entries
    for entry in feed.entries[:10]:  # limit to first 10
        print(entry.title)
        # print(entry.link)
        print(entry.published)
        # print entry.summary if it exists and is not empty 
        if 'summary' in entry and entry.summary:
            print(entry.summary)
        print()