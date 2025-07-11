#!/bin/bash

# Set the install path to a writable location
export PLAYWRIGHT_BROWSERS_PATH=/app/.playwright

# Force install chromium browser here
playwright install chromium

# Let Playwright know where the browser is
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=$(find /app/.playwright -name headless_shell | head -n 1)

echo "Chromium path: $PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"
echo "Starting Flask app..."
python app.py
