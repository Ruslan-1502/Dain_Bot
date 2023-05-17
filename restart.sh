#!/bin/bash

# Сохраняем базу данных в файл
heroku run python -c "import sqlite3; conn = sqlite3.connect('users.db'); conn.backup_to_file('users_backup.db')"

# Рестарт приложения
heroku restart --app dain

# Восстанавливаем базу данных из файла
heroku run python -c "import sqlite3; conn = sqlite3.connect('users.db'); backup = sqlite3.connect('users_backup.db'); backup.backup( conn )"
