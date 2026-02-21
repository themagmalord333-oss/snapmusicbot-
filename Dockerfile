FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Create config directory for instabot
RUN mkdir -p /app/config

# Environment variables
ENV PYTHONUNBUFFERED=1

# Start command
CMD ["./start.sh"]