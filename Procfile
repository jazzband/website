web: gunicorn --preload -w 4 jazzband.app:app --log-file=- --access-logfile=-
worker: celery worker -A jazzband.app:celery -E
