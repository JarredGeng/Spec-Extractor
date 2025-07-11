# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y curl wget gnupg libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxi6 libxrandr2 libxtst6 xvfb && \
    pip install --upgrade pip

# Copy everything into container
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Expose Flask port
EXPOSE 5001

# Run the app
CMD ["bash", "start.sh"]
