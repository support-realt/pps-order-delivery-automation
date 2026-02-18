# utils.py

import os
import json
import requests
from logger import logger
from constant import BASE_API_URL
from config_rts import load_config

config = load_config()





def get_download_dir():
    path = "/tmp"
    os.makedirs(path, exist_ok=True)
    return path


def get_token():
    try:
        logger.info("Getting Authentication token")
        url = f"{BASE_API_URL}/login/"
        payload = {"username": config.get("RTS_USERNAME"), "password": config.get("RTS_PASSWORD")}
        headers = {"content-type": "application/json"}
        response = requests.post(url, data=json.dumps(payload), headers=headers,  timeout=15 )
        logger.info("Token received successfully")
        return json.loads(response.content)["key"]
    except Exception as e:
        print(f"Error getting token: {e}")
        logger.exception("Error getting token")
        raise
