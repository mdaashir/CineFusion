# Dockerfile for CineFusion Backend

FROM python:3.11-slim

# Set environment variables for better Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python server.py health || exit 1

# Run the application
CMD ["python", "server.py", "start", "--host", "0.0.0.0", "--port", "8001"]
