"""生产环境 WSGI 入口：gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app"""
from app import create_app

app = create_app()
