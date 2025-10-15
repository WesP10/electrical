# Dockerfile for Cornell Hyperloop GUI
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r hyperloop && useradd -r -g hyperloop hyperloop

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R hyperloop:hyperloop /app

# Switch to non-root user
USER hyperloop

# Expose port
EXPOSE 8050

# Set environment variables
ENV DASH_HOST=0.0.0.0
ENV DASH_PORT=8050
ENV DASH_DEBUG=False
ENV PYTHONPATH=/app
ENV USE_MOCK_COMMUNICATION=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8050 || exit 1

# Run the application
CMD ["python", "src/app.py"]