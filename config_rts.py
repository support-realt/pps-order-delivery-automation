import os
from dotenv import load_dotenv

load_dotenv() 

def load_config():
    return {
        # PPS configuration
        "PPS_AUTH_KEY_3": os.environ.get("PPS_AUTH_KEY_3"),
        "PPS_ACC_1_USERNAME": os.environ.get("PPS_ACC_1_USERNAME"),
        "PPS_ACC_1_PASSWORD": os.environ.get("PPS_ACC_1_PASSWORD"),
        "PPS_ACC_2_USERNAME": os.environ.get("PPS_ACC_2_USERNAME"),
        "PPS_ACC_2_PASSWORD": os.environ.get("PPS_ACC_2_PASSWORD"),
        "PPS_MFA": os.environ.get("PPS_MFA"),
        "PPS_EMAIL_FROM": os.environ.get("PPS_EMAIL_FROM"),
        "PPS_EMAIL_FROM_PWD": os.environ.get("PPS_EMAIL_FROM_PWD"),

        # Non-PPS configuration
        "AUTH_KEY_3": os.environ.get("AUTH_KEY_3"),
        "ACC_1_USERNAME": os.environ.get("ACC_1_USERNAME"),
        "ACC_1_PASSWORD": os.environ.get("ACC_1_PASSWORD"),
        "ACC_2_USERNAME": os.environ.get("ACC_2_USERNAME"),
        "ACC_2_PASSWORD": os.environ.get("ACC_2_PASSWORD"),
        "MFA": os.environ.get("MFA"),
        "EMAIL_FROM": os.environ.get("EMAIL_FROM"),
        "EMAIL_FROM_PWD": os.environ.get("EMAIL_FROM_PWD"),
        "RTS_USERNAME" : os.environ.get("RTS_USERNAME"),
        "RTS_PASSWORD" : os.environ.get("RTS_PASSWORD"),
    }
