# Builder Stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy configuration files
COPY pyproject.toml poetry.lock ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Runtime Stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install system dependencies
# libgl1-mesa-glx: required by opencv-python
# libglib2.0-0: required by opencv-python
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from builder
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

# Expose port
EXPOSE 8080

# Health check (Optional but recommended)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8080/api/v1/health"]

# Run the application
CMD ["uvicorn", "posture_estimation.main:app", "--host", "0.0.0.0", "--port", "8080"]
