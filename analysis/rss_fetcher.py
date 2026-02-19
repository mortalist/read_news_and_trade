"""
RSS 뉴스 수집 모듈
여러 RSS 피드에서 뉴스를 수집하고 에러 처리 제공
"""
import feedparser
import time
from typing import List, Dict, Set
from datetime import datetime


class RSSFetcher:
    """RSS 피드에서 뉴스 수집 (중복 제거 및 캐싱 포함)"""

    def __init__(self, feed_urls: List[str], limit_per_feed: int = 5, cache_expiration_seconds: int = 3600):
        """
        Args:
            feed_urls: RSS 피드 URL 리스트
            limit_per_feed: 각 피드당 최대 수집 기사 수
            cache_expiration_seconds: 캐시 유지 시간 (초, 기본 1시간)
        """
        self.feed_urls = feed_urls
        self.limit_per_feed = limit_per_feed
        self.cache_expiration_seconds = cache_expiration_seconds
        self.cached_article_url_timestamps: Dict[str, float] = {}

    def fetch_all_news(self) -> List[Dict]:
        """
        모든 RSS 피드에서 새 뉴스만 수집

        중복 정책:
        - URL 기반: 완전히 동일한 링크는 캐시로 제거 (같은 기사 재수집 방지)
        - 제목 기반 중복 제거 제거됨: 여러 매체에서 같은 사건을 보도하면 각각 별도로 수집
          → 군중 심리 시뮬레이션: 동일 뉴스 반복 노출 = 더 많은 투자자 영향

        Returns:
            새 뉴스 기사 리스트 [{'title', 'published', 'summary', 'link', 'source'}, ...]
        """
        self._clean_cache()

        all_articles = []

        for feed_url in self.feed_urls:
            try:
                # RSS 피드 파싱
                feed = feedparser.parse(feed_url)

                # 파싱 오류 체크
                if feed.bozo:
                    print(f"⚠️ RSS 파싱 경고 [{feed_url}]: {feed.bozo_exception}")

                # 피드 소스 이름 추출 (피드 제목 또는 URL)
                source = feed.feed.get('title', feed_url)

                # 제한된 수만큼 기사 수집
                entries = feed.entries[:self.limit_per_feed]
                newly_collected_count = 0

                for entry in entries:
                    link = entry.get('link', '')
                    title = entry.get('title', 'No title')

                    # URL 기반 중복만 체크 (완전히 동일한 링크)
                    if link in self.cached_article_url_timestamps:
                        continue

                    article = {
                        'title': title,
                        'published': entry.get('published', 'Unknown date'),
                        'summary': entry.get('summary', entry.get('description', 'No summary')),
                        'link': link,
                        'source': source
                    }
                    all_articles.append(article)

                    self.cached_article_url_timestamps[link] = time.time()
                    newly_collected_count += 1

                if newly_collected_count > 0:
                    print(f"✅ [{source}] {newly_collected_count}개 새 기사 수집")
                else:
                    print(f"ℹ️ [{source}] 새 기사 없음 (캐시에 이미 존재)")

                # Rate limiting 방지
                time.sleep(0.5)

            except Exception as e:
                print(f"❌ RSS 수집 실패 [{feed_url}]: {e}")
                continue

        print(f"\n📊 총 {len(all_articles)}개 새 기사 수집 (URL 기반 캐싱, 제목 중복 허용)")
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

