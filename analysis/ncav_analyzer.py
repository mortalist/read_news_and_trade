"""
NCAV (Net Current Asset Value) 분석 모듈

벤자민 그레이엄(Benjamin Graham)의 NCAV 전략을 사용하여
기업의 저평가 여부를 판단하는 모듈입니다.
yfinance를 통해 재무제표 데이터를 가져와 NCAV 비율을 계산합니다.

NCAV Ratio = (Current Assets - Total Liabilities) / Current Assets

calculate_ncav_ratio(ticker: str, market: Optional[str] = None) -> Dict:
result = {
    'ticker': self.ticker,
    'ncav_ratio': ncav_ratio,
    'ncav_ratio_pct': ncav_ratio * 100,
    'current_assets': current_assets,
    'total_liabilities': total_liabilities,
    'net_current_assets': net_current_assets,
    'analysis_date': datetime.now().strftime('%Y-%m-%d'),
    'status': status,
    'interpretation': interpretation
}
"""
import os
import sys
from datetime import datetime
from typing import Dict, Optional
import pandas as pd
import numpy as np
import yfinance as yf


class NCAVAnalyzer:
    """NCAV (Net Current Asset Value) 분석기"""

    def __init__(self, ticker: str, market: Optional[str] = None):
        """
        Args:
            ticker: 종목 코드 (예: 'AAPL', 'MSFT')
            market: 시장 종류 (예: 'nyse', 'nasdaq') - 옵션
        """
        self.ticker = ticker.upper()
        self.market = market.lower() if market else None
        self.stock = None
        self.balance_sheet = None
        self.info = None

    def _fetch_data(self) -> bool:
        """
        yfinance를 통해 재무제표 데이터 수집

        Returns:
            bool: 데이터 수집 성공 여부
        """
        try:
            self.stock = yf.Ticker(self.ticker)

            # 재무상태표 데이터 가져오기
            self.balance_sheet = self.stock.balance_sheet

            # 데이터 유효성 검증
            if self.balance_sheet is None or self.balance_sheet.empty:
                return False

            return True

        except Exception as e:
            print(f"데이터 수집 중 오류 발생: {type(e).__name__}: {str(e)}")
            return False

    def _get_value(self, df: pd.DataFrame, key: str, year_index: int = 0) -> Optional[float]:
        """
        재무제표에서 특정 항목의 값 추출

        Args:
            df: 재무제표 DataFrame
            key: 항목 키
            year_index: 연도 인덱스 (0=최신, 1=전년)

        Returns:
            float 또는 None
        """
        try:
            if df is None or df.empty:
                return None

            # 연도 인덱스 범위 확인
            if year_index >= len(df.columns):
                return None

            # 키가 DataFrame의 인덱스에 있는지 확인
            if key in df.index:
                value = df.loc[key].iloc[year_index]
                return float(value) if pd.notna(value) else None

            return None

        except Exception as e:
            return None

    def _safe_divide(self, numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """
        안전한 나눗셈 (0으로 나누기 방지)

        Args:
            numerator: 분자
            denominator: 분모

        Returns:
            float 또는 None
        """
        if numerator is None or denominator is None:
            return None
        if denominator == 0:
            return None
        return numerator / denominator

    def _get_market_cap(self) -> Optional[float]:
        """
        시가총액을 여러 방법으로 시도하여 가져오기

        Returns:
            float 또는 None
        """
        try:
            # 방법 1: fast_info 사용 (가장 빠르고 안정적)
            try:
                market_cap = self.stock.fast_info.get('marketCap', None)
                if market_cap and market_cap > 0:
                    return float(market_cap)
            except Exception:
                pass

            # 방법 2: info 딕셔너리 사용
            try:
                market_cap = self.stock.info.get('marketCap', None)
                if market_cap and market_cap > 0:
                    return float(market_cap)
            except Exception:
                pass

            # 방법 3: 직접 계산 (주가 × 발행주식수)
            try:
                # 최신 주가 가져오기
                hist = self.stock.history(period="1d")
                if not hist.empty and 'Close' in hist.columns:
                    current_price = hist['Close'].iloc[-1]

                    # 발행주식수 가져오기
                    shares_outstanding = self._get_value(self.balance_sheet, 'Ordinary Shares Number', 0)

                    if current_price and shares_outstanding and shares_outstanding > 0:
                        return float(current_price * shares_outstanding)
            except Exception:
                pass

            # 모든 방법 실패
            return None

        except Exception as e:
            return None

    def calculate_ncav_ratio(self) -> Dict:
        """
        NCAV 비율 계산

        NCAV Ratio = (Current Assets - Total Liabilities) / Current Assets

        일반적으로:
        - NCAV Ratio > 0.5: 매우 건전한 유동성
        - NCAV Ratio > 0.3: 양호한 유동성
        - NCAV Ratio > 0: 기본적인 유동성 확보
        - NCAV Ratio < 0: 유동성 위험 (부채가 유동자산보다 많음)

        Returns:
            dict: {
                'ticker': 종목 코드,
                'ncav_ratio': NCAV 비율 (소수),
                'ncav_ratio_pct': NCAV 비율 (퍼센트),
                'current_assets': 유동자산,
                'total_liabilities': 총부채,
                'net_current_assets': 순유동자산 (Current Assets - Total Liabilities),
                'market_cap': 시가총액 (가능한 경우),
                'ncav_to_mcap': NCAV 대비 시가총액 비율 (Graham's NCAV 전략용),
                'analysis_date': 분석 일시,
                'status': 건전성 상태,
                'interpretation': 해석,
                'error': 에러 메시지 (에러 발생 시)
            }
        """
        # 데이터 수집
        if not self._fetch_data():
            return {
                'ticker': self.ticker,
                'ncav_ratio': None,
                'error': '재무제표 데이터를 가져올 수 없습니다.'
            }

        # 유동자산 추출
        current_assets = self._get_value(self.balance_sheet, 'Current Assets', 0)

        # 총부채 추출
        total_liabilities = self._get_value(self.balance_sheet, 'Total Liabilities Net Minority Interest', 0)

        # 데이터 검증
        if current_assets is None:
            return {
                'ticker': self.ticker,
                'ncav_ratio': None,
                'error': '유동자산(Current Assets) 데이터를 찾을 수 없습니다.'
            }

        if total_liabilities is None:
            return {
                'ticker': self.ticker,
                'ncav_ratio': None,
                'error': '총부채(Total Liabilities Net Minority Interest) 데이터를 찾을 수 없습니다.'
            }

        # NCAV 계산
        net_current_assets = current_assets - total_liabilities
        ncav_ratio = self._safe_divide(net_current_assets, current_assets)

        if ncav_ratio is None:
            return {
                'ticker': self.ticker,
                'ncav_ratio': None,
                'error': 'NCAV 비율 계산 실패 (유동자산이 0입니다).'
            }

        # 시가총액 가져오기 (Graham's NCAV 전략 확인용)
        market_cap = self._get_market_cap()
        ncav_to_mcap = None
        graham_ncav_signal = None

        if market_cap and net_current_assets > 0:
            ncav_to_mcap = net_current_assets / market_cap
            # Benjamin Graham의 NCAV 전략: 시가총액이 순유동자산보다 작은 경우 (NCAV > Market Cap)
            if ncav_to_mcap > 1.0:
                graham_ncav_signal = "Strong Buy - Graham's NCAV (Market Cap < Net Current Assets)"
            elif ncav_to_mcap > 0.67:
                graham_ncav_signal = "Potential Value - High NCAV/Market Cap Ratio"
            else:
                graham_ncav_signal = "No Graham NCAV Signal"

        # 건전성 판단
        if ncav_ratio >= 0.5:
            status = "Very Strong / Excellent Liquidity"
            interpretation = "유동자산이 총부채의 2배 이상으로 매우 건전합니다."
        elif ncav_ratio >= 0.3:
            status = "Strong / Good Liquidity"
            interpretation = "유동자산이 총부채보다 충분히 많아 건전한 상태입니다."
        elif ncav_ratio > 0:
            status = "Moderate / Fair Liquidity"
            interpretation = "유동자산이 총부채보다 많지만 여유는 적습니다."
        elif ncav_ratio == 0:
            status = "Neutral / Balanced"
            interpretation = "유동자산과 총부채가 같습니다."
        else:
            status = "Weak / Liquidity Risk"
            interpretation = "총부채가 유동자산보다 많아 유동성 위험이 있습니다."

        result = {
            'ticker': self.ticker,
            'ncav_ratio': ncav_ratio,
            'ncav_ratio_pct': ncav_ratio * 100,
            'current_assets': current_assets,
            'total_liabilities': total_liabilities,
            'net_current_assets': net_current_assets,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'status': status,
            'interpretation': interpretation
        }

        # 시가총액 관련 정보 추가 (있는 경우)
        if market_cap:
            result['market_cap'] = market_cap
            result['ncav_to_mcap'] = ncav_to_mcap
            result['graham_ncav_signal'] = graham_ncav_signal

        return result


# 편의 함수
def calculate_ncav_ratio(ticker: str, market: Optional[str] = None) -> Dict:
    """
    NCAV 비율 계산 (편의 함수)

    Args:
        ticker: 종목 코드 (예: 'AAPL', 'MSFT')
        market: 시장 종류 (예: 'nyse', 'nasdaq') - 옵션

    Returns:
        dict: NCAV 분석 결과

    Examples:
        >>> result = calculate_ncav_ratio('AAPL')
        >>> print(f"NCAV Ratio: {result['ncav_ratio_pct']:.2f}%")
        >>> print(f"Status: {result['status']}")
    """
    analyzer = NCAVAnalyzer(ticker, market)
    return analyzer.calculate_ncav_ratio()


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 80)
    print("NCAV (Net Current Asset Value) Analyzer 테스트")
    print("=" * 80)

    # 테스트 종목
    test_tickers = ['PLTR', 'MSFT', 'GOOGL', 'BRK.B', 'TSLA', 'AMZN', 'JNJ', 'V', 'WMT', 'JPM']

    for ticker in test_tickers:
        print(f"\n{'='*80}")
        print(f"종목: {ticker}")
        print(f"{'='*80}")

        result = calculate_ncav_ratio(ticker)
        
        if 'error' in result:
            print(f"❌ 오류: {result['error']}")
            continue

        print(f"\n📊 NCAV 비율: {result['ncav_ratio_pct']:.2f}%")
        print(f"📅 분석일: {result['analysis_date']}")
        print(f"🏥 상태: {result['status']}")
        print(f"💡 해석: {result['interpretation']}")

        print(f"\n📈 재무 데이터:")
        print(f"  • 유동자산 (Current Assets): ${result['current_assets']/1e9:.2f}B")
        print(f"  • 총부채 (Total Liabilities): ${result['total_liabilities']/1e9:.2f}B")
        print(f"  • 순유동자산 (Net Current Assets): ${result['net_current_assets']/1e9:.2f}B")

        print()
