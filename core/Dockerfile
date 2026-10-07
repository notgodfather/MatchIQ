FROM python:3.11-slim

# Install system dependencies (needed for lightgbm, psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (for docker layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Create directories for data and ensure permissions
RUN mkdir -p data/uploads data/db \
    && chmod -R 777 data

# Expose the port Render/Railway will route to
EXPOSE 8000

# Start the FastAPI backend
CMD ["uvicorn", "matchiq.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
