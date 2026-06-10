# 2 workers x 4 threads: the Claude AI call holds a thread for ~10s, so threads
# keep one user's AI pass from blocking everyone else on a small instance.
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
