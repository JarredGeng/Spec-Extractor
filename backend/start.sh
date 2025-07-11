#!/bin/bash

# Install Chromium to local path inside container
export PLAYWRIGHT_BROWSERS_PATH=0  # forces local install to /app/.playwright

echo "Installing Playwright Chromium..."
playwright install chromium

# Find installed Chromium path
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$(find .playwright -name headless_shell | head -n 1)

echo "Using Chromium from: $PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"

# Run your Flask app
python app.py
