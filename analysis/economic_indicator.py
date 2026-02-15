"""
FRED API를 사용한 경제 지표 추세 분석 모듈
경제 지표의 추세를 -3에서 +3 사이의 정수로 수치화
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import numpy as np
from scipy.stats import linregress
from fredapi import Fred

# secret.py에서 API 키 가져오기
try:
    # 프로젝트 루트 경로 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from secret import FRED_API_KEY as DEFAULT_FRED_API_KEY
except ImportError:
    DEFAULT_FRED_API_KEY = None


# 추세 점수 산출을 위한 임계값 (Threshold) 상수
# 나중에 조절 가능하도록 전역 변수로 분리
SLOPE_THRESHOLDS = {
    'strong_bullish': 0.5,      # slope > 0.5 -> +3
    'bullish': 0.2,             # 0.2 < slope <= 0.5 -> +2
    'mild_bullish': 0.05,       # 0.05 < slope <= 0.2 -> +1
    'neutral': 0.05,            # -0.05 <= slope <= 0.05 -> 0
    'mild_bearish': -0.05,      # -0.2 <= slope < -0.05 -> -1
    'bearish': -0.2,            # -0.5 <= slope < -0.2 -> -2
    'strong_bearish': -0.5      # slope < -0.5 -> -3
}

# 경제 지표 Ticker 매핑
INDICATOR_MAPPING = {
    'cpi': 'CPIAUCSL',                 # Consumer Price Index
    'pce': 'PCEPI',                    # Personal Consumption Expenditures
    'gdp': 'GDP',                      # Gross Domestic Product
    'unemployment': 'UNRATE',          # Unemployment Rate
    'interest': 'FEDFUNDS',            # Federal Funds Rate
    'retail': 'RSXFS',                 # Retail Sales
    'housing': 'HOUST',                # Housing Starts
    'industrial': 'INDPRO',            # Industrial Production
    'payroll': 'PAYEMS',               # Nonfarm Payrolls
    'ppi': 'PPIACO',                   # Producer Price Index
    'm2': 'M2SL',                      # M2 Money Supply
    'vix': 'VIXCLS',                   # VIX Volatility Index
}


class EconomicIndicatorAnalyzer:
    """FRED API를 사용한 경제 지표 추세 분석"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: FRED API 키 (미제공 시 secret.py의 FRED_API_KEY 사용)
        """
        if api_key is None:
            # 우선순위: 1) 파라미터 2) secret.py 3) 환경변수
            api_key = DEFAULT_FRED_API_KEY or os.environ.get('FRED_API_KEY')
            if not api_key:
                raise ValueError(
                    "FRED API 키가 필요합니다. "
                    "secret.py에 FRED_API_KEY를 설정하거나 "
                    "api_key 파라미터로 전달하세요."
                )

        self.fred = Fred(api_key=api_key)
        self.indicator_mapping = INDICATOR_MAPPING

    def _parse_period(self, period: str) -> datetime:
        """
        기간 문자열을 start_date로 변환

        Args:
            period: '1m', '3m', '6m', '1y', '3y', '5y' 등

        Returns:
            start_date (datetime)

        Raises:
            ValueError: 잘못된 기간 형식
        """
        period = period.lower().strip()
        now = datetime.now()

        # 기간 파싱
        if period.endswith('m'):
            # 월 단위
            try:
                months = int(period[:-1])
                start_date = now - timedelta(days=months * 30)
                return start_date
            except ValueError:
                raise ValueError(f"잘못된 기간 형식: {period}. 예: '1m', '3m', '6m'")

        elif period.endswith('y'):
            # 년 단위
            try:
                years = int(period[:-1])
                start_date = now - timedelta(days=years * 365)
                return start_date
            except ValueError:
                raise ValueError(f"잘못된 기간 형식: {period}. 예: '1y', '3y', '5y'")

        else:
            raise ValueError(
                f"지원하지 않는 기간 형식: {period}. "
                "'1m', '3m', '6m', '1y', '3y' 등의 형식을 사용하세요."
            )

    def _calculate_trend_score(self, series: pd.Series) -> tuple:
        """
        시계열 데이터의 추세 점수 계산

        알고리즘:
        1. 첫 번째 값 기준으로 100분율 정규화
        2. 선형 회귀로 기울기 계산
        3. 기울기에 따라 -3 ~ +3 점수 매핑

        Args:
            series: 경제 지표 시계열 데이터

        Returns:
            (slope, score): 기울기 및 추세 점수 (-3 ~ +3)
        """
        if series.empty or len(series) < 2:
            return 0.0, 0

        # NaN 제거
        series = series.dropna()

        if len(series) < 2:
            return 0.0, 0

        # 1. 첫 번째 값 기준으로 100분율 정규화
        start_value = series.iloc[0]

        if start_value == 0:
            # 0으로 나누기 방지
            return 0.0, 0

        normalized = (series / start_value) * 100

        # 2. 선형 회귀로 기울기 계산
        x = np.arange(len(normalized))
        y = normalized.values

        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # 3. 기울기에 따라 점수 매핑
        if slope > SLOPE_THRESHOLDS['strong_bullish']:
            score = 3
        elif slope > SLOPE_THRESHOLDS['bullish']:
            score = 2
        elif slope > SLOPE_THRESHOLDS['mild_bullish']:
            score = 1
        elif slope >= SLOPE_THRESHOLDS['mild_bearish']:
            score = 0
        elif slope >= SLOPE_THRESHOLDS['bearish']:
            score = -1
        elif slope >= SLOPE_THRESHOLDS['strong_bearish']:
            score = -2
        else:
            score = -3

        return slope, score

    def _get_trend_description(self, score: int) -> str:
        """
        점수에 대한 텍스트 설명 반환

        Args:
            score: 추세 점수 (-3 ~ +3)

        Returns:
            추세 설명 문자열
        """
        descriptions = {
            3: "Strong Bullish",
            2: "Bullish",
            1: "Mild Bullish",
            0: "Neutral",
            -1: "Mild Bearish",
            -2: "Bearish",
            -3: "Strong Bearish"
        }

        return descriptions.get(score, "Unknown")

    def get_economic_trend(
        self,
        indicator_alias: str,
        period: str
    ) -> Dict:
        """
        경제 지표의 추세를 분석하여 -3 ~ +3 점수 반환

        Args:
            indicator_alias: 지표 별칭 (예: 'cpi', 'gdp', 'unemployment')
            period: 분석 기간 (예: '1m', '3m', '6m', '1y', '3y')

        Returns:
            dict: {
                'indicator': 지표 별칭,
                'fred_series': FRED 시리즈 코드,
                'latest_value': 최신 값,
                'trend_score': 추세 점수 (-3 ~ +3),
                'trend_description': 추세 설명,
                'slope': 선형 회귀 기울기,
                'period': 분석 기간,
                'data_points': 데이터 포인트 개수,
                'error': 에러 메시지 (에러 발생 시)
            }

        Examples:
            >>> analyzer = EconomicIndicatorAnalyzer(api_key='your_api_key')
            >>> result = analyzer.get_economic_trend('cpi', '1y')
            >>> print(result)
            {
                'indicator': 'cpi',
                'fred_series': 'CPIAUCSL',
                'latest_value': 308.42,
                'trend_score': 2,
                'trend_description': 'Bullish',
                'slope': 0.35,
                'period': '1y',
                'data_points': 12
            }
        """
        # 입력 검증
        if not indicator_alias or not isinstance(indicator_alias, str):
            return {
                'indicator': indicator_alias,
                'error': '유효하지 않은 지표 이름입니다.'
            }

        if not period or not isinstance(period, str):
            return {
                'indicator': indicator_alias,
                'error': '유효하지 않은 기간입니다.'
            }

        # Ticker 매핑
        indicator_alias_lower = indicator_alias.lower()
        fred_series = self.indicator_mapping.get(indicator_alias_lower)

        if not fred_series:
            # 별칭이 없으면 그대로 사용 (직접 FRED 코드 입력한 경우)
            fred_series = indicator_alias.upper()

        try:
            # 기간 파싱
            start_date = self._parse_period(period)

            # FRED 데이터 조회
            series = self.fred.get_series(fred_series, observation_start=start_date)

            if series is None or series.empty:
                return {
                    'indicator': indicator_alias,
                    'fred_series': fred_series,
                    'error': f'데이터를 가져올 수 없습니다. (Series: {fred_series})'
                }

            # 최신 값
            latest_value = round(float(series.iloc[-1]), 2)

            # 추세 점수 계산
            slope, trend_score = self._calculate_trend_score(series)

            # 추세 설명
            trend_description = self._get_trend_description(trend_score)

            return {
                'indicator': indicator_alias,
                'fred_series': fred_series,
                'latest_value': latest_value,
                'trend_score': trend_score,
                'trend_description': trend_description,
                'slope': round(slope, 4),
                'period': period,
                'data_points': len(series)
            }

        except ValueError as e:
            return {
                'indicator': indicator_alias,
                'fred_series': fred_series if 'fred_series' in locals() else None,
                'error': str(e)
            }

        except Exception as e:
            return {
                'indicator': indicator_alias,
                'fred_series': fred_series if 'fred_series' in locals() else None,
                'error': f'예상치 못한 오류: {type(e).__name__}: {str(e)}'
            }


# 편의 함수
def get_economic_trend(
    indicator_alias: str,
    period: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    경제 지표의 추세를 분석하여 -3 ~ +3 점수 반환 (편의 함수)

    Args:
        indicator_alias: 지표 별칭 (예: 'cpi', 'gdp', 'unemployment')
        period: 분석 기간 (예: '1m', '3m', '6m', '1y', '3y')
        api_key: FRED API 키 (미제공 시 secret.py의 FRED_API_KEY 사용)

    Returns:
        dict: 추세 분석 결과

    Examples:
        >>> result = get_economic_trend('cpi', '1y')
        >>> print(f"CPI Trend: {result['trend_score']} ({result['trend_description']})")
    """
    analyzer = EconomicIndicatorAnalyzer(api_key=api_key)
    return analyzer.get_economic_trend(indicator_alias, period)


if __name__ == "__main__":
    """테스트 코드"""
    # 환경변수에서 API 키 로드 (또는 직접 입력)
    # import os
    # os.environ['FRED_API_KEY'] = 'your_api_key_here'

    print("=" * 60)
    print("FRED 경제 지표 추세 분석 테스트")
    print("=" * 60)

    # 사용 가능한 지표 출력
    print("\n[사용 가능한 지표]")
    for alias, series in INDICATOR_MAPPING.items():
        print(f"  - {alias:15} -> {series}")

    print("\n" + "=" * 60)
    print("테스트 실행 예시:")
    print("=" * 60)
    print("""
# API 키 설정
import os
os.environ['FRED_API_KEY'] = 'your_api_key_here'

# 분석 실행
from analysis.economic_indicator import get_economic_trend

# CPI 1년 추세
result = get_economic_trend('cpi', '1y')
print(result)

# 실업률 3개월 추세
result = get_economic_trend('unemployment', '3m')
print(result)

# GDP 3년 추세
result = get_economic_trend('gdp', '3y')
print(result)
""")
    # 실제 테스트 실행
    print("\n[실제 테스트 실행]")
    print(get_economic_trend('m2', '1y'))
