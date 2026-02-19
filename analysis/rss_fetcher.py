"""
RSS 뉴스 수집 모듈
여러 RSS 피드에서 뉴스를 수집하고 에러 처리 제공
"""
import feedparser
import time
import calendar
from typing import List, Dict, Set, Optional
from datetime import datetime


class RSSFetcher:
    """RSS 피드에서 뉴스 수집 (중복 제거 및 캐싱 포함)"""

    def __init__(self, feed_urls: List[str], min_old_articles: int = 2,
                 old_article_threshold_hours: float = 20, cache_expiration_seconds: int = 3600):
        """
        Args:
            feed_urls: RSS 피드 URL 리스트
            min_old_articles: 수집 중단 조건 - 이 수보다 많은 오래된 기사가 모이면 중단
            old_article_threshold_hours: "오래된" 기사 기준 시간 (시간 단위, 기본 20시간)
            cache_expiration_seconds: 캐시 유지 시간 (초, 기본 1시간)
        """
        self.feed_urls = feed_urls
        self.min_old_articles = min_old_articles
        self.old_article_threshold_hours = old_article_threshold_hours
        self.cache_expiration_seconds = cache_expiration_seconds
        self.cached_article_url_timestamps: Dict[str, float] = {}

    def _get_article_age_hours(self, entry) -> Optional[float]:
        """피드 항목의 발행 시간으로부터 경과 시간(시간 단위) 계산

        Returns:
            경과 시간 (hours) 또는 파싱 불가 시 None
        """
        published_parsed = entry.get('published_parsed')
        if published_parsed is None:
            return None
        try:
            published_timestamp = calendar.timegm(published_parsed)
            age_seconds = time.time() - published_timestamp
            return age_seconds / 3600.0
        except Exception:
            return None

    def fetch_all_news(self) -> List[Dict]:
        """
        모든 RSS 피드에서 새 뉴스를 수집 (중복 제거 및 캐싱)
        각 피드별로 오래된 기사가 min_old_articles개보다 많이 모이면 해당 피드 수집 중단.
        조건을 충족하지 못하면 해당 피드의 기사를 전부 수집.

        Returns:
            새 뉴스 기사 리스트 [{'title', 'published', 'summary', 'link', 'source', 'age_hours'}, ...]
        """
        self._clean_cache()

        all_articles = []
        deduplicated_title_set: Set[str] = set()

        for feed_url in self.feed_urls:
            try:
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    print(f"⚠️ RSS 파싱 경고 [{feed_url}]: {feed.bozo_exception}")

                source = feed.feed.get('title', feed_url)
                newly_collected_count = 0
                feed_old_article_count = 0

                for entry in feed.entries:
                    link = entry.get('link', '')
                    title = entry.get('title', 'No title')

                    if link in self.cached_article_url_timestamps:
                        continue

                    normalized_title_key = title.lower().strip()[:100]
                    if normalized_title_key in deduplicated_title_set:
                        continue

                    deduplicated_title_set.add(normalized_title_key)

                    age_hours = self._get_article_age_hours(entry)

                    article = {
                        'title': title,
                        'published': entry.get('published', 'Unknown date'),
                        'summary': entry.get('summary', entry.get('description', 'No summary')),
                        'link': link,
                        'source': source,
                        'age_hours': age_hours
                    }
                    all_articles.append(article)

                    self.cached_article_url_timestamps[link] = time.time()
                    newly_collected_count += 1

                    if age_hours is not None and age_hours > self.old_article_threshold_hours:
                        feed_old_article_count += 1
                        if feed_old_article_count > self.min_old_articles:
                            print(f"🛑 [{source}] 오래된 기사 {feed_old_article_count}개 도달 "
                                  f"(>{self.min_old_articles}개, 기준: {self.old_article_threshold_hours}시간) "
                                  f"- 이 피드 수집 중단")
                            break

                if newly_collected_count > 0:
                    print(f"✅ [{source}] {newly_collected_count}개 새 기사 수집 "
                          f"(오래된 기사: {feed_old_article_count}개)")
                else:
                    print(f"ℹ️ [{source}] 새 기사 없음 (캐시에 이미 존재)")

                time.sleep(0.5)

            except Exception as e:
                print(f"❌ RSS 수집 실패 [{feed_url}]: {e}")
                continue

        # 전체 기사 나이 통계
        known_ages = [a['age_hours'] for a in all_articles if a['age_hours'] is not None]
        if known_ages:
            avg_age = sum(known_ages) / len(known_ages)
            max_age = max(known_ages)
            print(f"⏱️ 기사 나이 통계 - 평균: {avg_age:.1f}시간, 가장 오래된 기사: {max_age:.1f}시간")

        total_old = sum(1 for age in known_ages if age > self.old_article_threshold_hours)
        print(f"\n📊 총 {len(all_articles)}개 새 기사 수집 (오래된 기사: {total_old}개, "
              f"중복 제거 및 캐싱 완료)")
        return all_articles

    def _clean_cache(self):
        """오래된 캐시 항목 삭제"""
        current_timestamp = time.time()
        expired_article_urls = [
            article_url for article_url, cached_timestamp in self.cached_article_url_timestamps.items()
            if current_timestamp - cached_timestamp > self.cache_expiration_seconds
        ]

        for article_url in expired_article_urls:
            del self.cached_article_url_timestamps[article_url]

        if expired_article_urls:
            print(f"🧹 캐시 정리: {len(expired_article_urls)}개 항목 삭제")

