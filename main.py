"""
KISTrader 뉴스 분석 파이프라인
뉴스 수집 → AI 분석 → 거래 신호 생성

두 가지 모드:
1. 한국투자증권 모드 (USE_KIS_API: true) - 토큰 획득 + 신호 생성
2. 뉴스 분석 전용 모드 (USE_KIS_API: false) - 신호만 생성
"""
print("DEBUG: Starting main.py")
import os
import sys
import time
import yaml
import traceback
from datetime import datetime

from util import halionia_discord_hook
print("DEBUG: Imports successful")

# 설정 파일 로드 및 검증
def load_config():
    """config.yaml 로드 및 검증"""
    configuration_file_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if not os.path.exists(configuration_file_path):
        print("❌ config.yaml이 없습니다. config.yaml.example을 참고하여 생성하세요.")
        sys.exit(1)

    with open(configuration_file_path, 'r', encoding='utf-8') as f:
        configuration_settings = yaml.safe_load(f)

    mandatory_configuration_fields = ['OPENAI_API_KEY', 'RSS_FEEDS']
    for configuration_field in mandatory_configuration_fields:
        if not configuration_settings.get(configuration_field):
            print(f"❌ 필수 설정 누락: {configuration_field}")
            sys.exit(1)

    openai_api_key = configuration_settings.get('OPENAI_API_KEY', '')
    if not openai_api_key.startswith('sk-'):
        print(f"❌ OPENAI_API_KEY 형식 오류: 'sk-'로 시작해야 합니다")
        sys.exit(1)

    rss_feed_url_list = configuration_settings.get('RSS_FEEDS')
    if not isinstance(rss_feed_url_list, list) or len(rss_feed_url_list) == 0:
        print("❌ RSS_FEEDS는 비어있지 않은 리스트여야 합니다")
        sys.exit(1)

    supported_openai_models = ['gpt-5-nano','gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4']
    selected_openai_model = configuration_settings.get('OPENAI_MODEL', 'gpt-4o-mini')
    if selected_openai_model not in supported_openai_models:
        print(f"⚠️ 경고: {selected_openai_model}은 유효하지 않을 수 있습니다. 권장 모델: {', '.join(supported_openai_models)}")

    if configuration_settings.get('NUM_LONG_POSITIONS', 2) < 1:
        print("❌ NUM_LONG_POSITIONS는 1 이상이어야 합니다")
        sys.exit(1)

    if configuration_settings.get('NUM_SHORT_POSITIONS', 1) < 1:
        print("❌ NUM_SHORT_POSITIONS는 1 이상이어야 합니다")
        sys.exit(1)

    if configuration_settings.get('LOOP_INTERVAL', 900) < 10:
        print("⚠️ 경고: LOOP_INTERVAL이 10초 미만입니다. API 비용이 매우 높아질 수 있습니다.")

    if configuration_settings.get('USE_KIS_API', False):
        required_kis_fields = ['APP_KEY', 'APP_SECRET', 'CANO', 'ACNT_PRDT_CD', 'URL_BASE']
        missing_configuration_fields = [configuration_field for configuration_field in required_kis_fields if not configuration_settings.get(configuration_field)]
        if missing_configuration_fields:
            print(f"❌ USE_KIS_API: true이지만 필수 설정 누락: {', '.join(missing_configuration_fields)}")
            print("   뉴스 분석 전용 모드로 사용하려면 USE_KIS_API: false로 설정하세요")
            sys.exit(1)

    if configuration_settings.get('USE_DISCORD', False):
        if not configuration_settings.get('DISCORD_WEBHOOK_URL'):
            print("❌ USE_DISCORD: true이지만 DISCORD_WEBHOOK_URL이 없습니다")
            sys.exit(1)

    print("✅ 설정 검증 완료")
    return configuration_settings


# 알림 전송 함수
def send_notification(msg, config, discord_enabled=False):
    """
    Discord 또는 콘솔로 알림 전송

    Args:
        msg: 메시지
        config: 설정 dict
        discord_enabled: Discord 사용 여부
    """
    print(msg)  # 항상 콘솔에 출력

    if discord_enabled and config.get('USE_DISCORD', False):
        try:
            import requests
            now = datetime.now()
            message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
            requests.post(config['DISCORD_WEBHOOK_URL'], data=message)

            #halionia discord webhook 사용
            import util.halionia_discord_hook
            halionia_discord_hook.halionia_send_wo_t_message(msg)

        except Exception as e:
            print(f"⚠️ Discord 전송 실패: {e}")


# 모듈 초기화
def initialize_modules(config):
    """
    RSS Fetcher, News Analyzer, Signal Generator 초기화

    Returns:
        (rss_fetcher, news_analyzer, signal_generator) 튜플
    """
    print("DEBUG: initialize_modules() called")
    print("DEBUG: Importing RSSFetcher...")
    from analysis.rss_fetcher import RSSFetcher
    print("DEBUG: Importing NewsAnalyzer...")
    from analysis.news_analyzer import NewsAnalyzer
    print("DEBUG: Importing SignalGenerator...")
    from trading.signal_generator import SignalGenerator
    print("DEBUG: All imports successful")

    # RSS Fetcher
    rss_fetcher = RSSFetcher(
        feed_urls=config['RSS_FEEDS'],
        min_old_articles=config.get('MIN_OLD_ARTICLES', 2),
        old_article_threshold_hours=config.get('OLD_ARTICLE_THRESHOLD_HOURS', 20)
    )

    # News Analyzer
    news_analyzer = NewsAnalyzer(
        api_key=config['OPENAI_API_KEY'],
        model=config.get('OPENAI_MODEL', 'gpt-4o-mini'),
        temperature=config.get('OPENAI_TEMPERATURE', 0.3),
        reasoning_effort=config.get('OPENAI_REASONING_EFFORT', {"effort": "medium"}),
        max_retries=config.get('MAX_RETRIES', 3),
        retry_delay=config.get('RETRY_DELAY', 2)
    )

    # Signal Generator
    signal_generator = SignalGenerator(
        num_long=config.get('NUM_LONG_POSITIONS', 2),
        num_short=config.get('NUM_SHORT_POSITIONS', 1)
    )

    return rss_fetcher, news_analyzer, signal_generator


# 파이프라인 실행
def run_pipeline(rss_fetcher, news_analyzer, signal_generator, config, kis_mode=False):
    """
    전체 파이프라인 실행
    1. RSS 수집
    2. AI 분석
    3. 신호 생성
    4. (TODO) 실제 매매

    Args:
        rss_fetcher: RSSFetcher 인스턴스
        news_analyzer: NewsAnalyzer 인스턴스
        signal_generator: SignalGenerator 인스턴스
        config: 설정 dict
        kis_mode: 한투 API 모드 여부
    """
    discord_enabled = config.get('USE_DISCORD', False)

    try:
        # 1. RSS 수집
        send_notification("📰 뉴스 수집 시작...", config, discord_enabled)
        articles = rss_fetcher.fetch_all_news()

        if not articles:
            send_notification("⚠️ 수집된 뉴스가 없습니다. 다음 주기를 기다립니다.", config, discord_enabled)
            return

        send_notification(f"✅ RSS 수집 완료 ({len(articles)}개 기사)", config, discord_enabled)

        # 2. AI 분석
        send_notification("🤖 AI 분석 시작...", config, discord_enabled)
        scorechart = news_analyzer.analyze_batch(articles)

        # 점수 요약
        score_summary = ", ".join([f"{sector}: {score}" for sector, score in sorted(scorechart.items(), key=lambda x: x[1], reverse=True)[:11]])
        send_notification(f"✅ 분석 완료\n섹터 점수: {score_summary}", config, discord_enabled)

        # 3. 신호 생성
        send_notification("📊 거래 신호 생성 중...", config, discord_enabled)
        signals = signal_generator.generate_signals(scorechart)
        signal_msg = signal_generator.format_signal_message(signals)
        send_notification(signal_msg, config, discord_enabled)

        # 4. 실제 매매 (TODO)
        if kis_mode:
            send_notification("📝 TODO: 실제 매매 실행 (미구현)", config, discord_enabled)
        else:
            send_notification("💡 신호를 확인하고 수동으로 매매하세요", config, discord_enabled)

    except Exception as e:
        error_msg = f"❌ 파이프라인 오류:\n{traceback.format_exc()}"
        send_notification(error_msg, config, discord_enabled)


# 메인 함수
def main():
    """메인 실행 함수"""
    print("DEBUG: main() function called")
    print("\n" + "="*60)
    print("KISTrader 뉴스 분석 파이프라인")
    print("="*60 + "\n")

    # 설정 로드
    print("DEBUG: Loading config...")
    config = load_config()
    print("DEBUG: Config loaded successfully")
    discord_enabled = config.get('USE_DISCORD', False)

    # 모드 확인 및 토큰 획득
    kis_mode = False
    ACCESS_TOKEN = None

    if config.get('USE_KIS_API', False):
        # 한국투자증권 모드
        try:
            from trading import token_fetch
            send_notification("🔐 한투 API 토큰 획득 시도 중...", config, discord_enabled)
            ACCESS_TOKEN = token_fetch.get_access_token()

            if ACCESS_TOKEN and ACCESS_TOKEN != "":
                send_notification("✅ 토큰 획득 완료 - 한투 모드 활성화", config, discord_enabled)
                send_notification("===해외 주식 자동매매 프로그램을 시작합니다===", config, discord_enabled)
                kis_mode = True
            else:
                send_notification("❌ 토큰 획득 실패 - 뉴스 분석 전용 모드로 전환", config, discord_enabled)
                kis_mode = False

        except Exception as e:
            send_notification(f"❌ 토큰 획득 오류: {e}\n뉴스 분석 전용 모드로 전환", config, discord_enabled)
            kis_mode = False
    else:
        # 뉴스 분석 전용 모드
        send_notification("📊 뉴스 분석 전용 모드로 시작", config, discord_enabled)
        kis_mode = False

    # 모듈 초기화
    try:
        print("DEBUG: Starting module initialization...")
        send_notification("⚙️ 모듈 초기화 중...", config, discord_enabled)
        print("DEBUG: Calling initialize_modules...")
        rss_fetcher, news_analyzer, signal_generator = initialize_modules(config)
        print("DEBUG: initialize_modules returned successfully")
        send_notification("✅ 모듈 초기화 완료", config, discord_enabled)
    except Exception as e:
        send_notification(f"❌ 모듈 초기화 실패:\n{traceback.format_exc()}", config, discord_enabled)
        sys.exit(1)

    # 무한 루프
    loop_interval = config.get('LOOP_INTERVAL', 900)  # 기본값 15분
    iteration = 0

    try:
        while True:
            iteration += 1
            send_notification(f"\n{'='*60}\n🔄 반복 #{iteration} 시작\n{'='*60}", config, discord_enabled)

            # 파이프라인 실행
            run_pipeline(rss_fetcher, news_analyzer, signal_generator, config, kis_mode)

            # 현재는 iteration 없이 종료
            exit()

            # 대기 - 미구현
            send_notification(f"\n⏳ {loop_interval}초 대기 중... (Ctrl+C로 종료)", config, discord_enabled)
            time.sleep(loop_interval)

    except KeyboardInterrupt:
        send_notification("\n\n👋 프로그램을 종료합니다.", config, discord_enabled)
        sys.exit(0)

    except Exception as e:
        send_notification(f"❌ 치명적 오류:\n{traceback.format_exc()}", config, discord_enabled)
        sys.exit(1)


if __name__ == "__main__":
    main()
