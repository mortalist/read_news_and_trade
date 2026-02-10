"""
AI 뉴스 분석 모듈
OpenAI API를 사용하여 뉴스 기사의 섹터별 감정 점수 분석
"""
import json
import time
import sys
from typing import Dict, List
from collections import Counter
from openai import OpenAI
import openai


# 11개 섹터 및 대응 ETF
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


class NewsAnalyzer:
    """OpenAI를 사용한 뉴스 감정 분석"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델 (기본: gpt-4o-mini)
            temperature: 응답 랜덤성 (0.0~1.0)
            max_retries: API 오류 시 재시도 횟수
            retry_delay: 재시도 간격 (초)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.SECTORS = SECTORS

    def analyze_article(self, article_text: str, article_source: str = "Unknown",
                       article_date: str = "Unknown") -> Dict[str, int]:
        """
        단일 기사 분석

        Args:
            article_text: 분석할 기사 텍스트 (제목 + 요약)
            article_source: 기사 출처
            article_date: 기사 날짜

        Returns:
            섹터별 감정 점수 dict (예: {'Technology': 3, 'Energy': -2, ...})
            실패 시 모든 섹터 0점 반환
        """
        prompt = f"""You are a financial analyst specializing in US stock market sentiment analysis. Analyze this news article and rate its potential impact on 11 US market sectors.

SCORING GUIDELINES:
+5: Extremely bullish (e.g., "Major breakthrough", "Record earnings beat 50%+", "Game-changing regulation")
+3: Moderately bullish (e.g., "Positive outlook", "Revenue increase 10-20%", "New partnerships")
+1: Slightly bullish (e.g., "Minor positive news", "Small price increases")
 0: Neutral or unclear impact (e.g., "General market news", "Unrelated to sector")
-1: Slightly bearish (e.g., "Minor concerns", "Small delays")
-3: Moderately bearish (e.g., "Disappointing results", "Regulatory warnings", "Supply chain issues")
-5: Extremely bearish (e.g., "Major crisis", "Bankruptcy concerns", "Severe regulations")

SECTOR DEFINITIONS:
1. Technology (XLK): Software companies, IT services, hardware manufacturers (EXCLUDING semiconductors)
   - Examples: Microsoft, Apple, Oracle, IBM
2. Semiconductors (SMH): Chip manufacturers, semiconductor equipment makers
   - Examples: NVIDIA, Intel, AMD, TSMC, ASML
3. Financials (XLF): Banks, insurance, investment firms, payment processors
   - Examples: JPMorgan, Bank of America, Visa, Mastercard
4. Healthcare (XLV): Pharmaceuticals, biotech, medical devices, healthcare services
   - Examples: Pfizer, Johnson & Johnson, UnitedHealth
5. Energy (XLE): Oil & gas, renewable energy, energy equipment
   - Examples: Exxon, Chevron, ConocoPhillips
6. Airlines (JETS): Commercial airlines, air cargo
   - Examples: American Airlines, Delta, United, Southwest
7. Consumer Discretionary (XLY): Retail, entertainment, automotive, luxury goods
   - Examples: Amazon, Tesla, Nike, McDonald's
8. Consumer Staples (XLP): Food, beverages, household products, tobacco
   - Examples: Coca-Cola, Procter & Gamble, Walmart groceries
9. Commodities (DBC): Agricultural products, metals, raw materials
   - Examples: Wheat, corn, copper, gold
10. Utilities (XLU): Electric, gas, water utilities, renewable infrastructure
    - Examples: Duke Energy, Southern Company, NextEra Energy
11. Real Estate (XLRE): REITs, real estate development, property management
    - Examples: American Tower, Prologis, Simon Property

NEWS ARTICLE:
Source: {article_source}
Date: {article_date}

{article_text}

IMPORTANT:
- Consider both DIRECT impact (mentioned in article) and INDIRECT impact (supply chain, competition)
- If a sector is not mentioned or affected, use 0
- Be conservative: most news affects 2-4 sectors significantly, others should be 0 or ±1

Return ONLY valid JSON with ALL 11 sectors:
{{"Technology": 0, "Semiconductors": 0, "Financials": 0, "Healthcare": 0, "Energy": 0, "Airlines": 0, "Consumer Discretionary": 0, "Consumer Staples": 0, "Commodities": 0, "Utilities": 0, "Real Estate": 0}}
"""

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a financial analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )

                api_response_content = response.choices[0].message.content
                sector_sentiment_scores = json.loads(api_response_content)

                # 모든 섹터가 포함되어 있는지 확인 및 기본값 설정
                for sector in SECTORS.keys():
                    if sector not in sector_sentiment_scores:
                        sector_sentiment_scores[sector] = 0

                return sector_sentiment_scores

            except openai.RateLimitError as rate_limit_exception:
                progressive_wait_seconds = (attempt + 1) * 10
                print(f"⚠️ OpenAI Rate Limit (시도 {attempt + 1}/{self.max_retries})")
                print(f"   {progressive_wait_seconds}초 대기 중...")
                if attempt < self.max_retries - 1:
                    time.sleep(progressive_wait_seconds)
                else:
                    print(f"❌ Rate Limit 초과 - 0점 반환")

            except openai.AuthenticationError as auth_exception:
                print(f"❌ OpenAI 인증 실패: {auth_exception}")
                print("   OPENAI_API_KEY를 확인하세요")
                sys.exit(1)

            except (openai.APIError, openai.Timeout, openai.APIConnectionError) as api_exception:
                exception_class_name = type(api_exception).__name__
                print(f"⚠️ OpenAI {exception_class_name} (시도 {attempt + 1}/{self.max_retries}): {api_exception}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ API 오류 (최종) - 0점 반환")

            except json.JSONDecodeError as json_exception:
                print(f"⚠️ JSON 파싱 실패 (시도 {attempt + 1}/{self.max_retries})")
                try:
                    print(f"   응답 내용: {api_response_content[:200]}")
                except:
                    pass
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ JSON 파싱 실패 (최종) - 0점 반환")

            except Exception as unexpected_exception:
                exception_class_name = type(unexpected_exception).__name__
                print(f"⚠️ 예상치 못한 오류 (시도 {attempt + 1}/{self.max_retries}): {exception_class_name}: {unexpected_exception}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ AI 분석 최종 실패 - 0점 반환")

        return {sector: 0 for sector in SECTORS.keys()}

    def analyze_batch(self, articles: List[Dict]) -> Dict[str, int]:
        """
        여러 기사 배치 분석

        Args:
            articles: 기사 리스트 [{'title', 'summary', 'source', 'published', ...}, ...]

        Returns:
            섹터별 점수 합계 dict (예: {'Technology': 25, 'Energy': -12, ...})
        """
        accumulated_sector_scores = Counter()

        for article_index, article in enumerate(articles, 1):
            formatted_article_content = f"Title: {article['title']}\n\nSummary: {article['summary']}"
            news_source_name = article.get('source', 'Unknown')
            publication_date = article.get('published', 'Unknown')

            print(f"🤖 분석 중... ({article_index}/{len(articles)}) [{news_source_name}]")

            sector_sentiment_scores = self.analyze_article(formatted_article_content, news_source_name, publication_date)

            accumulated_sector_scores.update(sector_sentiment_scores)

            # Rate limiting 방지
            time.sleep(1)

        return dict(accumulated_sector_scores)
