from trading import token_fetch
from util import discord_hook
import time

try:
    ACCESS_TOKEN = token_fetch.get_access_token()
    if ACCESS_TOKEN != "":
        print("ACCESS_TOKEN retrieved, beginning next sequence")
        discord_hook.send_message("ACCESS TOKEN retrieved, beginning next sequence")


    discord_hook.send_message("===해외 주식 자동매매 프로그램을 시작합니다===")
    while True:
        #main trading function
        
        #exit program
        break

except Exception as e:
    discord_hook.send_message(f"[오류 발생]{e}")
    time.sleep(1)