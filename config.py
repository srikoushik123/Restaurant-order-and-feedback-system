import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-this-in-production'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'restaurant_user'
    MYSQL_PASSWORD = 'restaurant123'
    MYSQL_DB = 'restaurant_db'
    MYSQL_CURSORCLASS = 'DictCursor'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)