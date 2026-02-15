from datetime import datetime, timezone
import feedparser

# RSS feed URLs to test
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

HOURS_THRESHOLD = 300
REQUIRED_OLD_ENTRIES = 1

print("=" * 80)
print(f"Testing RSS Feeds: Finding {REQUIRED_OLD_ENTRIES} entries older than {HOURS_THRESHOLD} hours")
print(f"Current time: {datetime.now(timezone.utc)}")
print("=" * 80)

results = []

for url in urls:
    try:
        # Parse the feed
        feed = feedparser.parse(url)

        if feed.bozo:
            print(f"\n⚠️  Warning parsing feed: {url}")
            print(f"   Error: {feed.bozo_exception}")

        # Get feed title
        feed_title = feed.feed.get('title', url)

        # Count entries until we find three entries older than threshold
        entries_count = 0
        old_entries_found = 0
        old_entries_info = []

        for entry in feed.entries:
            entries_count += 1

            # Calculate time delta
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                time_delta = datetime.now(timezone.utc) - published_time
                hours_old = time_delta.total_seconds() / 3600

                # Check if this entry is older than threshold
                if hours_old >= HOURS_THRESHOLD:
                    old_entries_found += 1
                    old_entries_info.append({
                        'position': entries_count,
                        'hours_old': hours_old
                    })

                    # Stop when we find the required number of old entries
                    if old_entries_found >= REQUIRED_OLD_ENTRIES:
                        break

        # Store and print results
        found_all = old_entries_found >= REQUIRED_OLD_ENTRIES
        result = {
            'feed_title': feed_title,
            'url': url,
            'entries_until_target': entries_count if found_all else None,
            'old_entries_found': old_entries_found,
            'old_entries_info': old_entries_info,
            'total_entries': len(feed.entries),
            'found': found_all
        }
        results.append(result)

        print(f"\n📰 {feed_title}")
        print(f"   URL: {url}")
        if found_all:
            print(f"   ✅ Found {REQUIRED_OLD_ENTRIES} entries older than {HOURS_THRESHOLD}h")
            print(f"   📊 Total entries checked to find them: {entries_count}")
            for i, info in enumerate(old_entries_info, 1):
                print(f"      Entry #{i}: position {info['position']}, age {info['hours_old']:.2f}h")
        else:
            print(f"   ❌ Only found {old_entries_found}/{REQUIRED_OLD_ENTRIES} entries older than {HOURS_THRESHOLD}h")
            print(f"   📊 Total entries checked: {len(feed.entries)}")
            if old_entries_info:
                for i, info in enumerate(old_entries_info, 1):
                    print(f"      Entry #{i}: position {info['position']}, age {info['hours_old']:.2f}h")

    except Exception as e:
        print(f"\n❌ Error processing {url}")
        print(f"   Error: {e}")
        results.append({
            'feed_title': url,
            'url': url,
            'entries_until_18h': None,
            'oldest_entry_hours': None,
            'total_entries': 0,
            'found': False,
            'error': str(e)
        })

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

feeds_with_old_entries = [r for r in results if r['found']]
feeds_without_old_entries = [r for r in results if not r['found']]

if feeds_with_old_entries:
    avg_entries = sum(r['entries_until_target'] for r in feeds_with_old_entries) / len(feeds_with_old_entries)
    print(f"\n✅ Feeds with {REQUIRED_OLD_ENTRIES} entries older than {HOURS_THRESHOLD}h: {len(feeds_with_old_entries)}/{len(results)}")
    print(f"📊 Average entries to find {REQUIRED_OLD_ENTRIES} old entries: {avg_entries:.1f}")
    print(f"📈 Min: {min(r['entries_until_target'] for r in feeds_with_old_entries)}")
    print(f"📈 Max: {max(r['entries_until_target'] for r in feeds_with_old_entries)}")

if feeds_without_old_entries:
    print(f"\n❌ Feeds without {REQUIRED_OLD_ENTRIES} entries older than {HOURS_THRESHOLD}h: {len(feeds_without_old_entries)}/{len(results)}")
    for r in feeds_without_old_entries:
        print(f"   - {r['feed_title']} ({r['old_entries_found']}/{REQUIRED_OLD_ENTRIES} found, {r['total_entries']} total entries)")

print("\n" + "=" * 80)