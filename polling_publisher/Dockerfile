FROM python:3.13-slim

# Ensure that Python doesn't write .pyc files
# and the stdout and stderr streams are sent straight to terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application code
COPY . .

# Copy requirements and install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the Message Relay
CMD ["python", "relay.py"]
