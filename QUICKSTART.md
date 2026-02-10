# 빠른 시작 가이드

## 5분 안에 시작하기

### 1. 의존성 설치 (1분)

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 생성 (2분)

```bash
cp config.yaml.example config.yaml
```

config.yaml을 열고 최소한 다음만 수정:

```yaml
OPENAI_API_KEY: "sk-your-actual-openai-api-key-here"
```

**중요**: `sk-your-actual-openai-api-key-here`를 실제 OpenAI API 키로 교체하세요.

### 3. 실행 (1분)

```bash
python main.py
```

종료하려면 `Ctrl+C`를 누르세요.

---

## 첫 실행 체크리스트

### ✅ 정상 동작 시 보이는 메시지:

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
...
```

### ❌ 문제 해결

**"config.yaml이 없습니다"**
```bash
cp config.yaml.example config.yaml
```

**"OPENAI_API_KEY가 설정되지 않았습니다"**
- config.yaml을 열고 실제 API 키로 수정

**"API 오류" 또는 "Invalid API key"**
- OpenAI API 키 확인: https://platform.openai.com/api-keys
- config.yaml에 정확히 복사했는지 확인

**"RSS 수집 실패"**
- 인터넷 연결 확인
- 일부 피드 실패는 정상 (다른 피드 계속 수집)

---

## 설정 옵션 (선택 사항)

### Discord 알림 활성화

config.yaml:
```yaml
USE_DISCORD: true
DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

### 한국투자증권 API 사용

config.yaml:
```yaml
USE_KIS_API: true
APP_KEY: "your-app-key"
APP_SECRET: "your-app-secret"
CANO: "your-account-number"
ACNT_PRDT_CD: "01"
```

### 실행 주기 변경

config.yaml:
```yaml
LOOP_INTERVAL: 60  # 60초 (1분)마다 실행
```

### API 비용 절감

config.yaml:
```yaml
NEWS_LIMIT_PER_FEED: 3  # 피드당 3개만 수집 (기본: 5)
```

---

## 다음 단계

- 자세한 설명: [README.md](README.md)
- 문제 발생 시: GitHub Issues
- 설정 템플릿: [config.yaml.example](config.yaml.example)

---

## 자주 묻는 질문

**Q: OpenAI API 비용이 얼마나 드나요?**
A: 기사당 약 $0.0001~0.0002 (gpt-4o-mini 기준). 40개 기사 분석 시 약 $0.004~0.008입니다.

**Q: 실제 매매가 되나요?**
A: 아니요. 현재는 신호만 생성합니다. 실제 매매는 나중에 추가될 예정입니다.

**Q: 어떤 ETF를 추천하나요?**
A: 11개 섹터 중 감정 점수가 높은 2개 (Long), 낮은 1개 (Short)를 선정합니다.

**Q: 15초마다 실행되는 게 너무 빠른데요?**
A: config.yaml에서 `LOOP_INTERVAL`을 300 (5분), 900 (15분) 등으로 조정하세요.

**Q: Discord 없이 사용 가능한가요?**
A: 네, 기본 설정(USE_DISCORD: false)으로 콘솔에만 출력됩니다.
