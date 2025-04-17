import requests

TOKEN = '7334373491:AAGp_FxEOXa18iOMTCdNYsNOYkcFBvob3ls'
WEBHOOK_URL = 'https://4302-102-218-50-52.ngrok-free.app/telegram/webhook/'

response = requests.get(f'https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}')
print(response.json())
