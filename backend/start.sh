#!/bin/bash
echo "Installing Playwright browsers..."
playwright install --with-deps

echo "Starting Flask app..."
python app.py
