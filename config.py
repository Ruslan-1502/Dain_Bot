import os

HEROKU_APP_NAME = os.getenv('dain')
BOT_TOKEN = '5905267839:AAGjbqOOXQlSAPYPQZj7TWx5rCf-DDWeDT0'
WEBHOOK_URL = f'https://dain.herokuapp.com/webhook/5905267839:AAGjbqOOXQlSAPYPQZj7TWx5rCf-DDWeDT'
WEBAPP_HOST = 'https://dain.herokuapp.com'
WEBAPP_PORT = os.environ.get('PORT')
WEBHOOK_PATH = '/webhook/5905267839:AAGjbqOOXQlSAPYPQZj7TWx5rCf-DDWeDT0'
