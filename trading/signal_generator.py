"""
거래 신호 생성 모듈
섹터별 감정 점수를 바탕으로 Long/Short ETF 선정
"""
from typing import Dict
from datetime import datetime
import pytz


# 섹터와 ETF 매핑
SECTOR_TO_ETF = {
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


class SignalGenerator:
    """거래 신호 생성기 (절대적 임계값 및 신뢰도 검증 포함)"""

    def __init__(self, num_long: int = 2, num_short: int = 1,
                 long_threshold: int = 5, short_threshold: int = -5,
                 min_score_diff: int = 3):
        """
        Args:
            num_long: Long 포지션 개수
            num_short: Short 포지션 개수
            long_threshold: Long 신호 최소 점수 (기본 +5)
            short_threshold: Short 신호 최대 점수 (기본 -5)
            min_score_diff: 같은 방향 포지션 간 최소 점수 차이 (기본 3)
        """
        self.num_long = num_long
        self.num_short = num_short
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.min_score_diff = min_score_diff

    def generate_signals(self, scorechart: Dict[str, int]) -> Dict:
        """
        섹터 점수를 바탕으로 거래 신호 생성 (절대적 임계값 및 신뢰도 검증)

        Args:
            scorechart: 섹터별 점수 dict (예: {'Technology': 25, 'Energy': -12, ...})

        Returns:
            거래 신호 dict:
            {
                'action': 'TRADE' | 'HOLD' | 'WEAK_SIGNAL',
                'confidence': 'HIGH' | 'MEDIUM' | 'LOW',
                'long_etfs': [ETF 코드 리스트] 또는 [],
                'long_sectors': [섹터 이름 리스트] 또는 [],
                'long_scores': [점수 리스트] 또는 [],
                'short_etf': ETF 코드 또는 None,
                'short_sector': 섹터 이름 또는 None,
                'short_score': 점수 또는 None,
                'timestamp': 생성 시각,
                'warnings': [경고 메시지 리스트],
                'all_scores': 전체 점수 (디버깅용)
            }
        """
        sectors_sorted_by_score = sorted(scorechart.items(), key=lambda x: x[1], reverse=True)

        eastern_timezone = pytz.timezone('America/New_York')
        signal_generation_timestamp = datetime.now(eastern_timezone).strftime('%Y-%m-%d %H:%M:%S %Z')

        signal_warnings = []

        long_eligible_sectors = [(sector, score) for sector, score in sectors_sorted_by_score
                          if score >= self.long_threshold]

        short_eligible_sectors = [(sector, score) for sector, score in sectors_sorted_by_score
                           if score <= self.short_threshold]

        if not long_eligible_sectors and not short_eligible_sectors:
            return {
                'action': 'HOLD',
                'confidence': 'N/A',
                'reason': f'유의미한 신호 없음 (Long 임계값: {self.long_threshold}, Short 임계값: {self.short_threshold})',
                'long_etfs': [],
                'long_sectors': [],
                'long_scores': [],
                'short_etf': None,
                'short_sector': None,
                'short_score': None,
                'timestamp': signal_generation_timestamp,
                'warnings': [],
                'all_scores': sectors_sorted_by_score
            }

        selected_long_positions = []
        if len(long_eligible_sectors) >= self.num_long:
            selected_long_positions = long_eligible_sectors[:self.num_long]

            if len(selected_long_positions) >= 2:
                top_two_score_difference = selected_long_positions[0][1] - selected_long_positions[1][1]
                if top_two_score_difference < self.min_score_diff:
                    signal_warnings.append(f"Long 포지션 간 점수 차이 작음 ({top_two_score_difference}점 < {self.min_score_diff}점)")

        elif len(long_eligible_sectors) > 0:
            selected_long_positions = long_eligible_sectors
            signal_warnings.append(f"Long 후보 부족 (요구: {self.num_long}개, 실제: {len(long_eligible_sectors)}개)")

        selected_short_position = None
        if len(short_eligible_sectors) >= self.num_short:
            selected_short_position = short_eligible_sectors[-1]
        elif len(short_eligible_sectors) > 0:
            selected_short_position = short_eligible_sectors[-1]
            signal_warnings.append(f"Short 후보 부족 (요구: {self.num_short}개, 실제: {len(short_eligible_sectors)}개)")

        signal_confidence = self._calculate_confidence(selected_long_positions, selected_short_position, signal_warnings)

        long_etf_tickers = [SECTOR_TO_ETF[sector] for sector, _ in selected_long_positions]
        long_sector_names = [sector for sector, _ in selected_long_positions]
        long_sector_scores = [score for _, score in selected_long_positions]

        short_etf_ticker = SECTOR_TO_ETF[selected_short_position[0]] if selected_short_position else None
        short_sector_name = selected_short_position[0] if selected_short_position else None
        short_sector_score = selected_short_position[1] if selected_short_position else None

        trading_action = 'WEAK_SIGNAL' if signal_warnings else 'TRADE'

        return {
            'action': trading_action,
            'confidence': signal_confidence,
            'long_etfs': long_etf_tickers,
            'long_sectors': long_sector_names,
            'long_scores': long_sector_scores,
            'short_etf': short_etf_ticker,
            'short_sector': short_sector_name,
            'short_score': short_sector_score,
            'timestamp': signal_generation_timestamp,
            'warnings': signal_warnings,
            'all_scores': sectors_sorted_by_score
        }

    def _calculate_confidence(self, selected_long_positions, selected_short_position, signal_warnings):
        """신뢰도 계산"""
        if signal_warnings:
            return 'LOW'

        high_confidence_score_threshold = 15

        has_high_confidence_long = any(score >= high_confidence_score_threshold for _, score in selected_long_positions)
        has_high_confidence_short = selected_short_position and selected_short_position[1] <= -high_confidence_score_threshold

        if has_high_confidence_long or has_high_confidence_short:
            return 'HIGH'
        else:
            return 'MEDIUM'

    def format_signal_message(self, signals: Dict) -> str:
        """
        Discord 알림용 메시지 포맷팅

        Args:
            signals: generate_signals()의 반환값

        Returns:
            포맷팅된 메시지 문자열
        """
        formatted_message = "=== 거래 신호 생성 완료 ===\n"
        formatted_message += f"⏰ {signals['timestamp']}\n"
        formatted_message += f"📊 액션: {signals['action']} | 신뢰도: {signals.get('confidence', 'N/A')}\n\n"

        if signals['action'] == 'HOLD':
            formatted_message += f"💤 {signals.get('reason', '거래 신호 없음')}\n"
            formatted_message += f"\n📊 섹터 점수 (상위 5개):\n"
            for sector_name, sector_score in signals['all_scores'][:5]:
                formatted_message += f"  • {sector_name}: {sector_score:+d}점\n"
            return formatted_message

        if signals.get('warnings'):
            formatted_message += "⚠️ 경고:\n"
            for warning_message in signals['warnings']:
                formatted_message += f"  • {warning_message}\n"
            formatted_message += "\n"

        if signals['long_etfs']:
            formatted_message += "📈 LONG 포지션:\n"
            for etf_ticker, sector_name, sector_score in zip(signals['long_etfs'], signals['long_sectors'], signals['long_scores']):
                formatted_message += f"  • {etf_ticker} ({sector_name}): {sector_score}점\n"
        else:
            formatted_message += "📈 LONG 포지션: 없음\n"

        formatted_message += f"\n📉 SHORT 포지션:\n"
        if signals['short_etf']:
            formatted_message += f"  • {signals['short_etf']} ({signals['short_sector']}): {signals['short_score']}점\n"
        else:
            formatted_message += "  • 없음\n"

        formatted_message += f"\n📊 섹터 점수 (상위 5개):\n"
        for sector_name, sector_score in signals['all_scores'][:5]:
            formatted_message += f"  • {sector_name}: {sector_score}점\n"

        return formatted_message


if __name__ == "__main__":
    sample_scores = {
        "Technology": 25.1,
        "Semiconductors": 18,
        "Financials": 3,
        "Healthcare": -2,
        "Energy": -15,
        "Airlines": -8,
        "Consumer Discretionary": 7,
        "Consumer Staples": 1,
        "Commodities": -3,
        "Utilities": 0,
        "Real Estate": -6.3
    }

    generator = SignalGenerator()
    signals = generator.generate_signals(sample_scores)

    print(generator.format_signal_message(signals))

    print("\n--- Raw Signal Data ---")
    for key, value in signals.items():
        if key != "all_scores":
            print(f"  {key}: {value}")

