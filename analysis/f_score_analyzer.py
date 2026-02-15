"""
Piotroski F-Score 분석 모듈

조셉 피오트로스키(Joseph Piotroski)의 9가지 재무 지표를 사용하여
기업의 재무 건전성을 0~9점으로 산출하는 모듈입니다.
yfinance를 통해 최근 2개년도 재무제표를 비교 분석합니다.

calculate_f_score(ticker: str, market: Optional[str] = None) -> Dict:
"""
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf


class PiotroskiFScoreAnalyzer:
    """Piotroski F-Score 분석기"""

    def __init__(self, ticker: str, market: Optional[str] = None):
        """
        Args:
            ticker: 종목 코드 (예: 'AAPL', 'MSFT')
            market: 시장 종류 (예: 'nyse', 'nasdaq') - 옵션
        """
        self.ticker = ticker.upper()
        self.market = market.lower() if market else None
        self.stock = None
        self.financials = None
        self.balance_sheet = None
        self.cashflow = None
        self.info = None

    def _fetch_data(self) -> bool:
        """
        yfinance를 통해 재무제표 데이터 수집

        Returns:
            bool: 데이터 수집 성공 여부
        """
        try:
            self.stock = yf.Ticker(self.ticker)

            # 재무제표 데이터 가져오기
            self.financials = self.stock.financials  # 손익계산서
            self.balance_sheet = self.stock.balance_sheet  # 재무상태표
            self.cashflow = self.stock.cashflow  # 현금흐름표
            self.info = self.stock.info

            # 데이터 유효성 검증
            if self.financials is None or self.financials.empty:
                return False
            if self.balance_sheet is None or self.balance_sheet.empty:
                return False
            if self.cashflow is None or self.cashflow.empty:
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

    # ==================== A. 수익성 (Profitability) - 4점 ====================

    def _check_positive_roa(self) -> Tuple[int, str]:
        """
        1. ROA (Return on Assets) > 0

        Returns:
            (점수, 설명)
        """
        net_income = self._get_value(self.financials, 'Net Income', 0)
        total_assets = self._get_value(self.balance_sheet, 'Total Assets', 0)

        roa = self._safe_divide(net_income, total_assets)

        if roa is None:
            return 0, "ROA: 데이터 없음"

        if roa > 0:
            return 1, f"ROA: {roa*100:.2f}% (양수) ✓"
        else:
            return 0, f"ROA: {roa*100:.2f}% (음수) ✗"

    def _check_positive_cfo(self) -> Tuple[int, str]:
        """
        2. CFO (Operating Cash Flow) > 0

        Returns:
            (점수, 설명)
        """
        cfo = self._get_value(self.cashflow, 'Operating Cash Flow', 0)

        if cfo is None:
            return 0, "CFO: 데이터 없음"

        if cfo > 0:
            return 1, f"CFO: ${cfo/1e9:.2f}B (양수) ✓"
        else:
            return 0, f"CFO: ${cfo/1e9:.2f}B (음수) ✗"

    def _check_roa_improvement(self) -> Tuple[int, str]:
        """
        3. ΔROA: 당해 ROA > 전년 ROA

        Returns:
            (점수, 설명)
        """
        # 당해 ROA
        net_income_current = self._get_value(self.financials, 'Net Income', 0)
        total_assets_current = self._get_value(self.balance_sheet, 'Total Assets', 0)
        roa_current = self._safe_divide(net_income_current, total_assets_current)

        # 전년 ROA
        net_income_prev = self._get_value(self.financials, 'Net Income', 1)
        total_assets_prev = self._get_value(self.balance_sheet, 'Total Assets', 1)
        roa_prev = self._safe_divide(net_income_prev, total_assets_prev)

        if roa_current is None or roa_prev is None:
            return 0, "ΔROA: 데이터 없음"

        if roa_current > roa_prev:
            return 1, f"ΔROA: {roa_current*100:.2f}% > {roa_prev*100:.2f}% (개선) ✓"
        else:
            return 0, f"ΔROA: {roa_current*100:.2f}% ≤ {roa_prev*100:.2f}% (악화) ✗"

    def _check_accruals(self) -> Tuple[int, str]:
        """
        4. Accruals: CFO > Net Income (현금흐름이 이익보다 많음)

        Returns:
            (점수, 설명)
        """
        cfo = self._get_value(self.cashflow, 'Operating Cash Flow', 0)
        net_income = self._get_value(self.financials, 'Net Income', 0)

        if cfo is None or net_income is None:
            return 0, "Accruals: 데이터 없음"

        if cfo > net_income:
            return 1, f"Accruals: CFO(${cfo/1e9:.2f}B) > NI(${net_income/1e9:.2f}B) ✓"
        else:
            return 0, f"Accruals: CFO(${cfo/1e9:.2f}B) ≤ NI(${net_income/1e9:.2f}B) ✗"

    # ==================== B. 재무구조 및 유동성 (Leverage/Liquidity) - 3점 ====================

    def _check_leverage_decrease(self) -> Tuple[int, str]:
        """
        5. ΔLeverage: 당해 장기부채비율 < 전년 장기부채비율

        Returns:
            (점수, 설명)
        """
        # 당해 장기부채비율
        long_term_debt_current = self._get_value(self.balance_sheet, 'Long Term Debt', 0) or 0
        total_assets_current = self._get_value(self.balance_sheet, 'Total Assets', 0)
        leverage_current = self._safe_divide(long_term_debt_current, total_assets_current)

        # 전년 장기부채비율
        long_term_debt_prev = self._get_value(self.balance_sheet, 'Long Term Debt', 1) or 0
        total_assets_prev = self._get_value(self.balance_sheet, 'Total Assets', 1)
        leverage_prev = self._safe_divide(long_term_debt_prev, total_assets_prev)

        if leverage_current is None or leverage_prev is None:
            return 0, "ΔLeverage: 데이터 없음"

        if leverage_current < leverage_prev:
            return 1, f"ΔLeverage: {leverage_current*100:.2f}% < {leverage_prev*100:.2f}% (개선) ✓"
        else:
            return 0, f"ΔLeverage: {leverage_current*100:.2f}% ≥ {leverage_prev*100:.2f}% (악화) ✗"

    def _check_liquidity_improvement(self) -> Tuple[int, str]:
        """
        6. ΔLiquid: 당해 유동비율 > 전년 유동비율

        Returns:
            (점수, 설명)
        """
        # 당해 유동비율
        current_assets_current = self._get_value(self.balance_sheet, 'Current Assets', 0)
        current_liabilities_current = self._get_value(self.balance_sheet, 'Current Liabilities', 0)
        liquid_current = self._safe_divide(current_assets_current, current_liabilities_current)

        # 전년 유동비율
        current_assets_prev = self._get_value(self.balance_sheet, 'Current Assets', 1)
        current_liabilities_prev = self._get_value(self.balance_sheet, 'Current Liabilities', 1)
        liquid_prev = self._safe_divide(current_assets_prev, current_liabilities_prev)

        if liquid_current is None or liquid_prev is None:
            return 0, "ΔLiquid: 데이터 없음"

        if liquid_current > liquid_prev:
            return 1, f"ΔLiquid: {liquid_current:.2f} > {liquid_prev:.2f} (개선) ✓"
        else:
            return 0, f"ΔLiquid: {liquid_current:.2f} ≤ {liquid_prev:.2f} (악화) ✗"

    def _check_no_new_shares(self) -> Tuple[int, str]:
        """
        7. EQ_Offer: 신주 발행 없음 (당해 발행주식수 ≤ 전년 발행주식수)

        Returns:
            (점수, 설명)
        """
        shares_current = self._get_value(self.balance_sheet, 'Ordinary Shares Number', 0)
        shares_prev = self._get_value(self.balance_sheet, 'Ordinary Shares Number', 1)

        if shares_current is None or shares_prev is None:
            return 0, "EQ_Offer: 데이터 없음"

        if shares_current <= shares_prev:
            return 1, f"EQ_Offer: {shares_current/1e9:.2f}B ≤ {shares_prev/1e9:.2f}B (발행 없음) ✓"
        else:
            return 0, f"EQ_Offer: {shares_current/1e9:.2f}B > {shares_prev/1e9:.2f}B (신주 발행) ✗"

    # ==================== C. 운영 효율성 (Operating Efficiency) - 2점 ====================

    def _check_margin_improvement(self) -> Tuple[int, str]:
        """
        8. ΔMargin: 당해 매출총이익률 > 전년 매출총이익률

        Returns:
            (점수, 설명)
        """
        # 당해 매출총이익률
        gross_profit_current = self._get_value(self.financials, 'Gross Profit', 0)
        revenue_current = self._get_value(self.financials, 'Total Revenue', 0)
        margin_current = self._safe_divide(gross_profit_current, revenue_current)

        # 전년 매출총이익률
        gross_profit_prev = self._get_value(self.financials, 'Gross Profit', 1)
        revenue_prev = self._get_value(self.financials, 'Total Revenue', 1)
        margin_prev = self._safe_divide(gross_profit_prev, revenue_prev)

        if margin_current is None or margin_prev is None:
            return 0, "ΔMargin: 데이터 없음"

        if margin_current > margin_prev:
            return 1, f"ΔMargin: {margin_current*100:.2f}% > {margin_prev*100:.2f}% (개선) ✓"
        else:
            return 0, f"ΔMargin: {margin_current*100:.2f}% ≤ {margin_prev*100:.2f}% (악화) ✗"

    def _check_turnover_improvement(self) -> Tuple[int, str]:
        """
        9. ΔTurnover: 당해 자산회전율 > 전년 자산회전율

        Returns:
            (점수, 설명)
        """
        # 당해 자산회전율
        revenue_current = self._get_value(self.financials, 'Total Revenue', 0)
        total_assets_current = self._get_value(self.balance_sheet, 'Total Assets', 0)
        turnover_current = self._safe_divide(revenue_current, total_assets_current)

        # 전년 자산회전율
        revenue_prev = self._get_value(self.financials, 'Total Revenue', 1)
        total_assets_prev = self._get_value(self.balance_sheet, 'Total Assets', 1)
        turnover_prev = self._safe_divide(revenue_prev, total_assets_prev)

        if turnover_current is None or turnover_prev is None:
            return 0, "ΔTurnover: 데이터 없음"

        if turnover_current > turnover_prev:
            return 1, f"ΔTurnover: {turnover_current:.2f} > {turnover_prev:.2f} (개선) ✓"
        else:
            return 0, f"ΔTurnover: {turnover_current:.2f} ≤ {turnover_prev:.2f} (악화) ✗"

    def calculate_f_score(self) -> Dict:
        """
        Piotroski F-Score 계산

        Returns:
            dict: {
                'ticker': 종목 코드,
                'f_score': F-Score (0~9),
                'breakdown': {
                    'profitability': (점수, 상세),
                    'leverage': (점수, 상세),
                    'efficiency': (점수, 상세)
                },
                'details': 각 항목별 상세 설명 리스트,
                'analysis_date': 분석 일시,
                'status': 건전성 상태,
                'error': 에러 메시지 (에러 발생 시)
            }
        """
        # 데이터 수집
        if not self._fetch_data():
            return {
                'ticker': self.ticker,
                'f_score': None,
                'error': '재무제표 데이터를 가져올 수 없습니다.'
            }

        # 9가지 항목 체크
        checks = [
            # A. 수익성 (4점)
            self._check_positive_roa(),
            self._check_positive_cfo(),
            self._check_roa_improvement(),
            self._check_accruals(),

            # B. 재무구조 및 유동성 (3점)
            self._check_leverage_decrease(),
            self._check_liquidity_improvement(),
            self._check_no_new_shares(),

            # C. 운영 효율성 (2점)
            self._check_margin_improvement(),
            self._check_turnover_improvement(),
        ]

        # 점수 합산
        total_score = sum(score for score, _ in checks)
        details = [desc for _, desc in checks]

        # 카테고리별 점수
        profitability_score = sum(score for score, _ in checks[0:4])
        leverage_score = sum(score for score, _ in checks[4:7])
        efficiency_score = sum(score for score, _ in checks[7:9])

        # 건전성 판단
        if total_score >= 7:
            status = "Strong / Healthy"
        elif total_score >= 5:
            status = "Moderate / Fair"
        elif total_score >= 3:
            status = "Weak / Caution"
        else:
            status = "Poor / High Risk"

        return {
            'ticker': self.ticker,
            'f_score': total_score,
            'breakdown': {
                'profitability': (profitability_score, 4),
                'leverage': (leverage_score, 3),
                'efficiency': (efficiency_score, 2)
            },
            'details': details,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'status': status
        }


# 편의 함수
def calculate_f_score(ticker: str, market: Optional[str] = None) -> Dict:
    """
    Piotroski F-Score 계산 (편의 함수)

    Args:
        ticker: 종목 코드 (예: 'AAPL', 'MSFT')
        market: 시장 종류 (예: 'nyse', 'nasdaq') - 옵션

    Returns:
        dict: F-Score 분석 결과

    Examples:
        >>> result = calculate_f_score('AAPL')
        >>> print(f"F-Score: {result['f_score']}/9")
        >>> print(f"Status: {result['status']}")
    """
    analyzer = PiotroskiFScoreAnalyzer(ticker, market)
    return analyzer.calculate_f_score()


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 80)
    print("Piotroski F-Score Analyzer 테스트")
    print("=" * 80)

    # 테스트 종목
    test_tickers = ['AAPL', 'MSFT', 'GOOGL',"BRK.B"]

    for ticker in test_tickers:
        print(f"\n{'='*80}")
        print(f"종목: {ticker}")
        print(f"{'='*80}")

        result = calculate_f_score(ticker)

        if 'error' in result:
            print(f"❌ 오류: {result['error']}")
            continue

        print(f"\n📊 F-Score: {result['f_score']}/9")
        print(f"📅 분석일: {result['analysis_date']}")
        print(f"🏥 상태: {result['status']}")

        print(f"\n📈 카테고리별 점수:")
        breakdown = result['breakdown']
        print(f"  • 수익성 (Profitability): {breakdown['profitability'][0]}/{breakdown['profitability'][1]}")
        print(f"  • 재무구조 (Leverage): {breakdown['leverage'][0]}/{breakdown['leverage'][1]}")
        print(f"  • 운영효율 (Efficiency): {breakdown['efficiency'][0]}/{breakdown['efficiency'][1]}")

        print(f"\n📋 세부 항목:")
        for i, detail in enumerate(result['details'], 1):
            print(f"  {i}. {detail}")

        print()
