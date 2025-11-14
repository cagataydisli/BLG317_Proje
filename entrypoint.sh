#!/bin/sh
set -e

echo "Waiting for database..."
python /app/wait_for_db.py

echo "Initializing database (init_db.py)..."
python /app/init_db.py

echo "Starting Flask..."
exec "$@"