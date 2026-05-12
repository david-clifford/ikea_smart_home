import os
from dotenv import load_dotenv
from dirigera import Hub

load_dotenv()

def get_hub():
    "Connect to DIRIGERA hub using environment variables"
    token, ip = os.getenv("DIRIGERA_TOKEN"), os.getenv("DIRIGERA_IP")
    assert token and ip, "DIRIGERA_TOKEN and DIRIGERA_IP must be set"
    return Hub(token=token, ip_address=ip)
