#!/bin/bash
set -e

echo "===== META-AI AUTO DEPLOY ====="

# Go to project root
cd /var/www/projects/meta-ai-campaign || exit 1

# Pull latest code
echo "Pulling latest code from GitHub..."
git pull origin main

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
  echo "Virtual environment not found. Exiting."
  exit 1
fi

# Install / update Python dependencies inside venv
echo "Installing Python dependencies..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Restart application service
echo "Restarting meta-ai service..."
systemctl daemon-reload
systemctl restart meta-ai.service

echo "Deploy completed successfully."
