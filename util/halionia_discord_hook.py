import datetime
import requests
import yaml
import os

config_path = os.path.join(os.path.dirname(__file__), 'halionia_discord_config.yaml')
with open(config_path, encoding='UTF-8') as f:
    discord_cfg = yaml.load(f, Loader=yaml.FullLoader)

DISCORD_WEBHOOK_URL = discord_cfg['DISCORD_WEBHOOK_URL']

def halionia_send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)
