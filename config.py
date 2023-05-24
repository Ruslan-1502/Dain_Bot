import os

BOT_TOKEN = '5905267839:AAGjbqOOXQlSAPYPQZj7TWx5rCf-DDWeDT0'
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.environ.get('PORT')
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'https://kilichev.pythonanywhere.com{WEBHOOK_PATH}'
