#!/bin/bash
export PLAYWRIGHT_BROWSERS_PATH=0  # forces install to local .playwright directory

echo "Installing Playwright browsers..."
playwright install chromium

echo "Starting Flask app..."
python app.py
