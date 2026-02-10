import feedparser

# Example RSS feed (BBC News)
# url = "http://feeds.bbci.co.uk/news/rss.xml"
url = "https://feeds.bloomberg.com/markets/news.rss"

# Parse the feed
feed = feedparser.parse(url)

# Print feed title
print(feed.feed.title)

# Loop through entries
for entry in feed.entries[:10]:  # limit to first 10
    print(entry.title)
    print(entry.link)
    print(entry.published)
    # print entry.summary if it exists and is not empty 
    if 'summary' in entry and entry.summary:
        print(entry.summary)
    print()