"""
Financial Statement Score (FS-Score) 분석 모듈

F-Score를 확장하여 '이익의 질(Quality of Earnings)'과
'분식회계 위험'을 중점적으로 평가하는 모듈입니다.
발생주의 회계의 허점을 필터링하는 데 목적이 있습니다.
F-Score 점수를 받아 작동함

calculate_fs_score(ticker: str, market: Optional[str] = None, f_score_result: Optional[Dict] = None)
"""
import os
import sys
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import pandas as pd
import numpy as np
import yfinance as yf

# F-Score 분석기 import
try:
    # 프로젝트 루트 경로 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from analysis.f_score_analyzer import PiotroskiFScoreAnalyzer
except ImportError:
    PiotroskiFScoreAnalyzer = None


class FSScoreAnalyzer:
    """Financial Statement Score (FS-Score) 분석기"""

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
            self.financials = self.stock.financials
            self.balance_sheet = self.stock.balance_sheet
            self.cashflow = self.stock.cashflow
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

            if year_index >= len(df.columns):
                return None

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

    # ==================== A. 회계적 보수주의 필터 (Conservatism) ====================

    def _check_accrual_intensity(self) -> Tuple[int, str, Optional[str]]:
        """
        Accrual Intensity: (CFO - NI) / Total Assets 비율 분석

        급격히 낮아지면(이익은 나는데 돈은 안 들어옴) 위험 신호

        Returns:
            (점수 조정, 설명, 위험 요인)
        """
        cfo_current = self._get_value(self.cashflow, 'Operating Cash Flow', 0)
        net_income_current = self._get_value(self.financials, 'Net Income', 0)
        total_assets_current = self._get_value(self.balance_sheet, 'Total Assets', 0)

        cfo_prev = self._get_value(self.cashflow, 'Operating Cash Flow', 1)
        net_income_prev = self._get_value(self.financials, 'Net Income', 1)
        total_assets_prev = self._get_value(self.balance_sheet, 'Total Assets', 1)

        # 당해 및 전년 Accrual Intensity 계산
        if all(v is not None for v in [cfo_current, net_income_current, total_assets_current]):
            accrual_current = (cfo_current - net_income_current) / total_assets_current
        else:
            accrual_current = None

        if all(v is not None for v in [cfo_prev, net_income_prev, total_assets_prev]):
            accrual_prev = (cfo_prev - net_income_prev) / total_assets_prev
        else:
            accrual_prev = None

        if accrual_current is None:
            return 0, "Accrual Intensity: 데이터 없음", None

        # 판단 기준: 당해 Accrual < -0.05 (현금 유입 < 이익) -> 위험
        if accrual_current < -0.05:
            risk = "High accrual intensity detected (Cash < Earnings)"
            if accrual_prev is not None and accrual_current < accrual_prev - 0.03:
                # 전년 대비 급격히 악화
                return -2, f"Accrual Intensity: {accrual_current:.3f} (급격히 악화) ⚠️", risk
            else:
                return -1, f"Accrual Intensity: {accrual_current:.3f} (위험) ⚠️", risk
        else:
            return 0, f"Accrual Intensity: {accrual_current:.3f} (정상) ✓", None

    def _check_receivables_vs_revenue(self) -> Tuple[int, str, Optional[str]]:
        """
        Receivables vs Revenue: 매출 증가율 대비 매출채권 증가율 분석

        매출채권 증가율이 매출 증가율보다 비정상적으로 높으면 '가공 매출' 가능성

        Returns:
            (점수 조정, 설명, 위험 요인)
        """
        revenue_current = self._get_value(self.financials, 'Total Revenue', 0)
        revenue_prev = self._get_value(self.financials, 'Total Revenue', 1)

        # yfinance에서 Accounts Receivable 키 이름 확인
        # 일반적으로 'Accounts Receivable' 또는 'Receivables'
        receivables_current = (
            self._get_value(self.balance_sheet, 'Accounts Receivable', 0) or
            self._get_value(self.balance_sheet, 'Receivables', 0)
        )
        receivables_prev = (
            self._get_value(self.balance_sheet, 'Accounts Receivable', 1) or
            self._get_value(self.balance_sheet, 'Receivables', 1)
        )

        if any(v is None for v in [revenue_current, revenue_prev, receivables_current, receivables_prev]):
            return 0, "Receivables vs Revenue: 데이터 없음", None

        if revenue_prev == 0 or receivables_prev == 0:
            return 0, "Receivables vs Revenue: 계산 불가", None

        revenue_growth = (revenue_current - revenue_prev) / revenue_prev
        receivables_growth = (receivables_current - receivables_prev) / receivables_prev

        # 판단 기준: 매출채권 증가율이 매출 증가율보다 20%p 이상 높으면 위험
        growth_diff = receivables_growth - revenue_growth

        if growth_diff > 0.20:
            risk = "High receivables growth detected (possible revenue manipulation)"
            return -2, f"Receivables Growth: {receivables_growth*100:.1f}% vs Revenue: {revenue_growth*100:.1f}% (차이 {growth_diff*100:.1f}%p) ⚠️", risk
        elif growth_diff > 0.10:
            risk = "Moderate receivables growth detected"
            return -1, f"Receivables Growth: {receivables_growth*100:.1f}% vs Revenue: {revenue_growth*100:.1f}% (차이 {growth_diff*100:.1f}%p) ⚠️", risk
        else:
            return 0, f"Receivables Growth: {receivables_growth*100:.1f}% vs Revenue: {revenue_growth*100:.1f}% (정상) ✓", None

    def _check_inventory(self) -> Tuple[int, str, Optional[str]]:
        """
        Inventory Check: 매출 대비 재고자산 비중 급증 확인

        재고자산 비중이 전년 대비 급증했는지 확인 (재고 밀어내기 확인)

        Returns:
            (점수 조정, 설명, 위험 요인)
        """
        revenue_current = self._get_value(self.financials, 'Total Revenue', 0)
        revenue_prev = self._get_value(self.financials, 'Total Revenue', 1)

        inventory_current = self._get_value(self.balance_sheet, 'Inventory', 0)
        inventory_prev = self._get_value(self.balance_sheet, 'Inventory', 1)

        if any(v is None for v in [revenue_current, revenue_prev]):
            return 0, "Inventory Check: 데이터 없음", None

        if inventory_current is None or inventory_prev is None:
            # 재고가 없는 서비스 기업일 수 있음
            return 0, "Inventory Check: 재고 없음 (서비스 기업)", None

        # 재고자산 회전율 계산
        inventory_to_revenue_current = self._safe_divide(inventory_current, revenue_current)
        inventory_to_revenue_prev = self._safe_divide(inventory_prev, revenue_prev)

        if inventory_to_revenue_current is None or inventory_to_revenue_prev is None:
            return 0, "Inventory Check: 계산 불가", None

        # 판단 기준: 재고/매출 비율이 전년 대비 30% 이상 증가하면 위험
        ratio_change = (inventory_to_revenue_current - inventory_to_revenue_prev) / inventory_to_revenue_prev

        if ratio_change > 0.30:
            risk = "Excessive inventory buildup detected"
            return -2, f"Inventory/Revenue: {inventory_to_revenue_current*100:.1f}% (전년 대비 {ratio_change*100:.1f}% 증가) ⚠️", risk
        elif ratio_change > 0.15:
            risk = "Moderate inventory buildup detected"
            return -1, f"Inventory/Revenue: {inventory_to_revenue_current*100:.1f}% (전년 대비 {ratio_change*100:.1f}% 증가) ⚠️", risk
        else:
            return 0, f"Inventory/Revenue: {inventory_to_revenue_current*100:.1f}% (정상) ✓", None

    # ==================== B. 수익의 지속성 (Sustainability) ====================

    def _check_one_time_items(self) -> Tuple[int, str, Optional[str]]:
        """
        One-time Items: 당기순이익 중 영업외이익 비중 확인

        영업외이익(자산매각 등) 비중이 20% 이상이면 수익성 재평가

        Returns:
            (점수 조정, 설명, 위험 요인)
        """
        net_income = self._get_value(self.financials, 'Net Income', 0)
        operating_income = self._get_value(self.financials, 'Operating Income', 0)

        if net_income is None or operating_income is None:
            return 0, "One-time Items: 데이터 없음", None

        if net_income == 0:
            return 0, "One-time Items: 순이익 0", None

        # 영업외이익 = 순이익 - 영업이익
        non_operating_income = net_income - operating_income
        non_operating_ratio = self._safe_divide(non_operating_income, net_income)

        if non_operating_ratio is None:
            return 0, "One-time Items: 계산 불가", None

        # 판단 기준: 영업외이익 비중이 20% 이상이면 주의
        if non_operating_ratio > 0.20:
            risk = "High non-operating income ratio (earnings quality concern)"
            return -1, f"Non-operating Income: {non_operating_ratio*100:.1f}% of Net Income ⚠️", risk
        elif non_operating_ratio < -0.20:
            # 영업외손실이 큰 경우도 주의
            risk = "High non-operating loss ratio"
            return -1, f"Non-operating Loss: {abs(non_operating_ratio)*100:.1f}% of Net Income ⚠️", risk
        else:
            return 0, f"Non-operating Income: {non_operating_ratio*100:.1f}% (정상) ✓", None

    def calculate_fs_score(self, f_score_result: Optional[Dict] = None) -> Dict:
        """
        FS-Score 계산

        Args:
            f_score_result: F-Score 분석 결과 (제공되지 않으면 자동 계산)

        Returns:
            dict: {
                'ticker': 종목 코드,
                'f_score': 기본 F-Score,
                'fs_score': 최종 FS-Score,
                'adjustments': 조정 내역,
                'risk_factors': 위험 요인 리스트,
                'details': 상세 설명 리스트,
                'analysis_date': 분석 일시,
                'status': 건전성 상태,
                'error': 에러 메시지 (에러 발생 시)
            }
        """
        # F-Score가 제공되지 않았으면 자동 계산
        if f_score_result is None:
            if PiotroskiFScoreAnalyzer is None:
                return {
                    'ticker': self.ticker,
                    'error': 'F-Score 분석기를 import할 수 없습니다.'
                }

            f_analyzer = PiotroskiFScoreAnalyzer(self.ticker, self.market)
            f_score_result = f_analyzer.calculate_f_score()

            if 'error' in f_score_result:
                return f_score_result

        # 데이터 수집 (FS-Score 전용 분석)
        if not self._fetch_data():
            return {
                'ticker': self.ticker,
                'f_score': f_score_result.get('f_score'),
                'fs_score': None,
                'error': '재무제표 데이터를 가져올 수 없습니다.'
            }

        base_f_score = f_score_result.get('f_score', 0)

        # 회계적 보수주의 및 수익 지속성 검사
        checks = [
            self._check_accrual_intensity(),
            self._check_receivables_vs_revenue(),
            self._check_inventory(),
            self._check_one_time_items(),
        ]

        # 조정 점수 합산
        total_adjustment = sum(score for score, _, _ in checks)
        details = [desc for _, desc, _ in checks]
        risk_factors = [risk for _, _, risk in checks if risk is not None]

        # 최종 FS-Score 계산 (단, 0점 이하로 떨어지지 않도록)
        final_fs_score = max(0, base_f_score + total_adjustment)

        # 건전성 판단
        if final_fs_score >= 7 and len(risk_factors) == 0:
            status = "Healthy / Low Risk"
        elif final_fs_score >= 5 and len(risk_factors) <= 1:
            status = "Fair / Moderate Risk"
        elif final_fs_score >= 3:
            status = "Caution / Elevated Risk"
        else:
            status = "High Risk / Poor Quality"

        return {
            'ticker': self.ticker,
            'f_score': base_f_score,
            'fs_score': final_fs_score,
            'adjustments': total_adjustment,
            'risk_factors': risk_factors,
            'details': details,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'status': status
        }


# 편의 함수
def calculate_fs_score(ticker: str, market: Optional[str] = None, f_score_result: Optional[Dict] = None) -> Dict:
    """
    FS-Score 계산 (편의 함수)

    Args:
        ticker: 종목 코드 (예: 'AAPL', 'MSFT')
        market: 시장 종류 (예: 'nyse', 'nasdaq') - 옵션
        f_score_result: F-Score 분석 결과 (제공되지 않으면 자동 계산)

    Returns:
        dict: FS-Score 분석 결과

    Examples:
        >>> result = calculate_fs_score('AAPL')
        >>> print(f"FS-Score: {result['fs_score']}")
        >>> print(f"Status: {result['status']}")
        >>> if result['risk_factors']:
        >>>     print("Risk Factors:")
        >>>     for risk in result['risk_factors']:
        >>>         print(f"  - {risk}")
    """
    analyzer = FSScoreAnalyzer(ticker, market)
    return analyzer.calculate_fs_score(f_score_result)


if __name__ == "__main__":
    """테스트 코드"""
    print("=" * 80)
    print("FS-Score Analyzer 테스트")
    print("=" * 80)

    # 테스트 종목
    test_tickers = ['AAPL', 'MSFT', 'TSLA']

    for ticker in test_tickers:
        print(f"\n{'='*80}")
        print(f"종목: {ticker}")
        print(f"{'='*80}")

        result = calculate_fs_score(ticker)

        if 'error' in result:
            print(f"❌ 오류: {result['error']}")
            continue

        print(f"\n📊 기본 F-Score: {result['f_score']}/9")
        print(f"📊 최종 FS-Score: {result['fs_score']}")
        print(f"🔧 조정: {result['adjustments']:+d}")
        print(f"📅 분석일: {result['analysis_date']}")
        print(f"🏥 상태: {result['status']}")

        if result['risk_factors']:
            print(f"\n⚠️  위험 요인:")
            for risk in result['risk_factors']:
                print(f"  • {risk}")
        else:
            print(f"\n✅ 위험 요인 없음")

        print(f"\n📋 세부 항목:")
        for i, detail in enumerate(result['details'], 1):
            print(f"  {i}. {detail}")

        print()
