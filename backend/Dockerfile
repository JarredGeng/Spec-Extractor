FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies for Playwright and system libs
RUN apt-get update && \
    apt-get install -y wget curl gnupg libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 \
    libxss1 libasound2 libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
    libxi6 libxrandr2 libxtst6 xvfb && \
    pip install --upgrade pip

# Copy project files
COPY . .

# Install Python requirements
RUN pip install -r requirements.txt

# Install Playwright and its browser dependencies
RUN pip install playwright && \
    playwright install --with-deps

# Expose the Flask port
EXPOSE 5001

# Start the app
CMD ["python", "app.py"]
