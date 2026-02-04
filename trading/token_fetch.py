import yaml
import os
import requests
import json
import datetime

config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
URL_BASE = _cfg['URL_BASE']
TOKEN_FILE = "token_info.json"

def get_access_token():
    """토큰 발급 및 로컬 캐싱 관리"""
    global ACCESS_TOKEN
    
    # 1. 기존 저장된 파일이 있는지 확인
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            
            # 저장된 발급 시간 문자열을 datetime 객체로 변환
            last_issued = datetime.datetime.strptime(token_data['issued_at'], "%Y-%m-%d %H:%M:%S")
            
            # 2. 시간 차이 계산 (현재 시간 - 마지막 발급 시간)
            if datetime.datetime.now() - last_issued < datetime.timedelta(hours=1):
                ACCESS_TOKEN = token_data['access_token']
                print(f"캐시 사용: 1시간 이내에 발급된 토큰을 재사용합니다. (발급시각: {token_data['issued_at']})")
                return ACCESS_TOKEN
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # 파일이 손상되었거나 형식이 다를 경우 새로 발급받도록 진행
            pass

    # 3. 1분이 지났거나 저장된 정보가 없으면 새로 발급 요청
    print("신규 요청: 1시간이 지났거나 정보가 없어 서버에서 새 토큰을 가져옵니다.")
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY, 
        "appsecret": APP_SECRET
    }
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    
    try:
        res = requests.post(URL, headers=headers, data=json.dumps(body))
        res_data = res.json()
        
        if "access_token" in res_data:
            # print(res_data["access_token"])
            ACCESS_TOKEN = res_data["access_token"]
            
            # 4. 새로운 토큰 정보와 현재 시간을 파일에 기록
            save_data = {
                "access_token": ACCESS_TOKEN,
                "issued_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(save_data, f, indent=4)
        
            return ACCESS_TOKEN

        else:
            print("토큰 발급 실패:", res_data.get("msg1", "알 수 없는 에러"))
            return None
            
    except Exception as e:
        print(f"네트워크 또는 기타 오류 발생: {e}")
        return None
