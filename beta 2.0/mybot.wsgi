import os
from main import app

# Установка переменной окружения для использования конфигурации из config.py
os.environ["MYAPP_CONFIG"] = "config.py"

# Создание WSGI-приложения
application = app
