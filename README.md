# KISTrader 뉴스 분석 파이프라인

뉴스 수집 → AI 분석 → 거래 신호 생성 자동화 시스템

## 특징

- **두 가지 모드**:
  1. **뉴스 분석 전용 모드**: OpenAI API만 사용 (신호만 생성, 수동 매매용)
  2. **한국투자증권 모드**: OpenAI + 한투 API (나중에 실제 매매 가능)

- **11개 섹터 분석**: Technology, Semiconductors, Financials, Healthcare, Energy, Airlines, Consumer Discretionary, Consumer Staples, Commodities, Utilities, Real Estate

- **자동 신호 생성**: 감정 점수 기반 Long 2개 / Short 1개 ETF 선정

- **선택적 Discord 알림**: 콘솔 전용 또는 Discord Webhook 사용

## 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 생성

```bash
cp config.yaml.example config.yaml
```

### 3. config.yaml 편집

#### 뉴스 분석 전용 모드 (권장 - 초기 테스트)

```yaml
USE_KIS_API: false
USE_DISCORD: false  # 또는 true + Webhook URL
OPENAI_API_KEY: "sk-your-actual-api-key"
```

#### 한국투자증권 모드 (한투 API 있는 경우)

```yaml
USE_KIS_API: true
USE_DISCORD: false
OPENAI_API_KEY: "sk-your-actual-api-key"
APP_KEY: "your-app-key"
APP_SECRET: "your-app-secret"
CANO: "your-account-number"
ACNT_PRDT_CD: "01"
```

## 사용 방법

### 기본 실행

```bash
python main.py
```

### 동작 순서

1. **뉴스 수집**: 8개 RSS 피드에서 최신 뉴스 수집
2. **AI 분석**: OpenAI로 각 기사의 섹터별 감정 점수 분석 (-5 ~ +5)
3. **신호 생성**: 점수 합산 후 상위 2개 Long, 하위 1개 Short ETF 선정
4. **알림**: 콘솔 또는 Discord로 거래 신호 전송
5. **대기**: 15초 후 다음 주기 시작

### 종료

```
Ctrl+C
```

## 출력 예시

```
============================================================
KISTrader 뉴스 분석 파이프라인
============================================================

📊 뉴스 분석 전용 모드로 시작
⚙️ 모듈 초기화 중...
✅ 모듈 초기화 완료

============================================================
🔄 반복 #1 시작
============================================================
📰 뉴스 수집 시작...
✅ [Bloomberg Markets] 5개 기사 수집
✅ [CNBC] 5개 기사 수집
✅ RSS 수집 완료 (40개 기사)

🤖 AI 분석 시작...
🤖 분석 중... (1/40) [Bloomberg Markets]
🤖 분석 중... (2/40) [CNBC]
...
✅ 분석 완료
섹터 점수 (상위 5개): Technology: +18, Semiconductors: +12, Healthcare: +5, Financials: +2, Consumer Staples: 0

📊 거래 신호 생성 중...
=== 거래 신호 생성 완료 ===
⏰ 2026-02-11 14:30:00 EST

📈 LONG 포지션:
  • XLK (Technology): +18점
  • SMH (Semiconductors): +12점

📉 SHORT 포지션:
  • XLE (Energy): -8점

📊 섹터 점수 (상위 5개):
  • Technology: +18점
  • Semiconductors: +12점
  • Healthcare: +5점
  • Financials: +2점
  • Consumer Staples: 0점

💡 신호를 확인하고 수동으로 매매하세요

⏳ 15초 대기 중... (Ctrl+C로 종료)
```

## 설정 파일 옵션

### 필수 설정 (모든 모드)

- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_MODEL`: 사용 모델 (기본: gpt-4o-mini)
- `RSS_FEEDS`: RSS 피드 URL 목록
- `NEWS_LIMIT_PER_FEED`: 피드당 최대 기사 수 (기본: 5)

### 선택 설정

- `USE_KIS_API`: 한투 API 사용 여부 (기본: false)
- `USE_DISCORD`: Discord 알림 사용 여부 (기본: false)
- `MAX_RETRIES`: API 재시도 횟수 (기본: 3)
- `LOOP_INTERVAL`: 실행 주기 초 (기본: 15)
- `NUM_LONG_POSITIONS`: Long 포지션 개수 (기본: 2)
- `NUM_SHORT_POSITIONS`: Short 포지션 개수 (기본: 1)

## 프로젝트 구조

```
.
├── main.py                    # 메인 파이프라인
├── config.yaml                # 설정 파일 (직접 생성)
├── config.yaml.example        # 설정 템플릿
├── requirements.txt           # Python 의존성
├── analysis/
│   ├── rss_fetcher.py        # RSS 뉴스 수집
│   └── news_analyzer.py      # OpenAI 감정 분석
├── trading/
│   ├── token_fetch.py        # 한투 토큰 획득 (기존)
│   └── signal_generator.py   # 거래 신호 생성
└── util/
    └── discord_hook.py       # Discord 알림 (기존)
```

## 에러 처리

- **RSS 피드 실패**: 개별 피드 실패 시 다른 피드 계속 수집
- **AI 분석 실패**: 최대 3회 재시도, 실패 시 0점 처리
- **파이프라인 실패**: 에러 로그 출력 후 다음 주기 계속 진행
- **치명적 오류**: 설정 파일 없음, API 키 무효 시 프로그램 종료

## 주의사항

1. **OpenAI API 비용**: 기사당 API 호출 발생 → `NEWS_LIMIT_PER_FEED`로 조절
2. **Rate Limiting**: 기사 분석 간 1초 딜레이 적용
3. **실제 매매 제외**: 현재는 신호만 생성 (TODO: 나중에 구현)
4. **보안**: `config.yaml`은 gitignore에 포함 (API 키 노출 방지)

## 향후 개선 (TODO)

- [ ] 실제 매매 로직 통합 (UsaStockAutoTradeRevise.py)
- [ ] 포지션 관리 및 리스크 관리
- [ ] 뉴스 중복 제거
- [ ] RSS 수집 병렬화
- [ ] 데이터베이스 저장 (뉴스, 신호 기록)
- [ ] 백테스팅 시스템

## 라이센스

개인 사용 목적
