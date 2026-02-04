import requests
import json
import datetime
from pytz import timezone
import time
import yaml
import os
import matplotlib.pyplot as plt

config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_access_token():
    """토큰 발급"""
    global ACCESS_TOKEN
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN
    
def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

def get_current_price(market="NASD", code="AAPL"):
    """현재가 조회"""
    PATH = "uapi/overseas-price/v1/quotations/price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"HHDFS00000300"}
    params = {
        "AUTH": "",
        "EXCD":market,
        "SYMB":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return float(res.json()['output']['last'])

def get_target_entry_price(market="NASD", code="AAPL"):
    """황금원 진입 지점 """
    PATH = "uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"HHDFS76240000"}
    params = {
        "AUTH":"",
        "EXCD":market,
        "SYMB":code,
        "GUBN":"0",
        "BYMD":"",
        "MODP":"0"
    }
    res = requests.get(URL, headers=headers, params=params)
    predayclose = float(res.json()['output2'][1]['clos']) #전일 종가
    predayhigh = float(res.json()['output2'][1]['high']) #전일 고가
    predaylow = float(res.json()['output2'][1]['low']) #전일 저가

    target_entry_price = ( predayhigh + predaylow + predayclose ) / 3 + (predayhigh - predaylow)
    return target_entry_price

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT3012R",
        "custtype":"P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['ovrs_cblc_qty']) > 0:
            stock_dict[stock['ovrs_pdno']] = stock['ovrs_cblc_qty']
            send_message(f"{stock['ovrs_item_name']}({stock['ovrs_pdno']}): {stock['ovrs_cblc_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: ${evaluation['tot_evlu_pfls_amt']}")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: ${evaluation['ovrs_tot_pfls']}")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

def buy(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 지정가 매수"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price,2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT1002U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매수 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

def sell(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 지정가 매도"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price,2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT1006U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매도 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False

def get_exchange_rate():
    """환율 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"CTRP6504R"}
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "WCRC_FRCR_DVSN_CD": "01",
        "NATN_CD": "840",
        "TR_MKET_CD": "01",
        "INQR_DVSN_CD": "00"
    }
    res = requests.get(URL, headers=headers, params=params)
    exchange_rate = 1270.0
    if len(res.json()['output2']) > 0:
        exchange_rate = float(res.json()['output2'][0]['frst_bltn_exrt'])
    return exchange_rate

def get_stock_five_minute_price(market="NAS", code="AAPL"):
    """주식 분봉 가격 조회"""
    PATH = "/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"HHDFS76950200"}
    params = {
        "AUTH":"",
        "EXCD":market,
        "SYMB":code,
        "NMIN":"5",
        "PIN":"1",
        "NEXT":"",
        "NREC":"120",
        "FIL":"",
        "KEYB":""
    }
    # 1) API 호출: 5분봉 120개(NREC=120) 요청
    res = requests.get(URL, headers=headers, params=params)

    # 2) 응답 JSON 파싱
    payload = res.json()

    # 3) 메시지 출력(정상 처리 여부 등)
    send_message(payload.get('msg1', ''))

    # 4) 디버깅/확인용: 응답 전체 JSON을 파일로 저장
    #    (나중에 output2 구조/필드명 확인할 때 유용)
    # with open('stock_five_minute_price.txt', 'w', encoding='utf-8') as f:
    #     json.dump(payload, f, ensure_ascii=False)

    # 5) 5분봉 데이터는 payload["output2"]에 리스트 형태로 들어옴
    #    예: [{"kymd":"20260128","khms":"090000","open":"258.1200", ...}, ...]
    candles = payload.get('output2', []) or []
    ts_open_list = []  # 반환 형태: [(timestamp, open_price), ...]

    # 6) 최대 120개만 추출해서 (timestamp, open) 튜플 리스트 생성
    for c in candles[:120]:
        # timestamp 만들기:
        # - 우선 KST 필드(kymd/khms)가 있으면 사용
        # - 없으면 거래소 시간 필드(xymd/xhms)로 대체
        # - 최종 형태: "YYYYMMDDHHMMSS" (문자열)
        ymd = (c.get('kymd') or c.get('xymd') or '').strip()
        hms = (c.get('khms') or c.get('xhms') or '').strip()
        ts = f"{ymd}{hms}" if (ymd and hms) else (ymd or hms or "")

        # open 가격은 문자열로 오므로 float로 변환
        # 변환 실패(필드 누락/값 이상)하면 해당 캔들은 스킵
        try:
            open_price = float(c.get('open'))
        except (TypeError, ValueError):
            continue

        # (timestamp, open_price) 형태로 리스트에 저장
        ts_open_list.append((ts, open_price))

        # 로그 출력: 나중에 확인하기 쉽도록 timestamp와 open을 함께 출력
        # (원하면 print 대신 send_message로 바꿔도 됨)
        print(f"{ts} open={open_price}")

    dates = [item[0] for item in ts_open_list]
    open_prices = [item[1] for item in ts_open_list]

        # 3. Create the plot
    plt.figure(figsize=(10, 5))
    plt.plot(dates, open_prices, marker='o', linestyle='-', color='b')

    # 4. Formatting the visuals
    plt.title("Price Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Price ($)")
    plt.grid(True)
    plt.xticks(rotation=45) # Rotates labels so they don't overlap
    plt.tight_layout()

    # 5. Display
    plt.show()

    # 7) 최종 반환: 120개 분봉의 (timestamp, open_price) 리스트
    return ts_open_list

# 자동매매 시작
try:
    ACCESS_TOKEN = get_access_token()
    if ACCESS_TOKEN != "":
        print("ACCESS_TOKEN retrieved, beginning next sequence")
        send_message("ACCESS TOKEN retrieved, beginning next sequence")
    

    #total_cash = get_balance() # 보유 현금 조회
    #send_message(total_cash)
    # nasd_symbol_list = ["AAPL"] # 매수 희망 종목 리스트 (NASD)
    # nyse_symbol_list = ["KO"] # 매수 희망 종목 리스트 (NYSE)
    # amex_symbol_list = ["LIT"] # 매수 희망 종목 리스트 (AMEX)
    # symbol_list = nasd_symbol_list + nyse_symbol_list + amex_symbol_list

    # stock_and_market_list = [["AAPL","NASD"],["KO","NYSE"]]

    # bought_list = [] # 매수 완료된 종목 리스트
    # exchange_rate = get_exchange_rate() # 환율 조회
    # stock_dict = get_stock_balance() # 보유 주식 조회
    # for sym in stock_dict.keys():
    #     bought_list.append(sym)
    # target_buy_count = 1 # 매수할 종목 수
    # buy_percent = 1 # 종목당 매수 금액 비율
    # #buy_amount = total_cash * buy_percent / exchange_rate # 종목별 주문 금액 계산 (달러)
    # soldout = False

    send_message("===해외 주식 자동매매 프로그램을 시작합니다===")
    while True:
        stock_five_minute_price = get_stock_five_minute_price("NAS","INTC")

        #wait 15 seconds
        time.sleep(15)
        #exit program
        break
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)