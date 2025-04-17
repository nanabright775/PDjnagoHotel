# config.py
BASE_URL = 'https://broadly-lenient-adder.ngrok-free.app/'
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_BOT_TOKEN=f'{TOKEN}'
