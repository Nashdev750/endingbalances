#!/bin/bash

# Find and kill gunicorn processes run by root
echo "Checking for root-owned gunicorn instances..."
PIDS=$(ps -u root -o pid,cmd | grep gunicorn | grep -v grep | awk '{print $1}')

if [ -n "$PIDS" ]; then
  echo "Killing gunicorn processes under root: $PIDS"
  kill -9 $PIDS
else
  echo "No root-owned gunicorn processes found."
fi

# Start new gunicorn instance with 4 workers on port 5000
echo "Starting new gunicorn instance (4 workers) on port 5000..."
# Replace 'app:app' with your actual WSGI app module
gunicorn app:app --bind 0.0.0.0:5000 --workers 4 --daemon

echo "Gunicorn started with 4 workers on port 5000."
