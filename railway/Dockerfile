FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install git for committing results back to repo
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (include README.md as required by pyproject.toml)
COPY pyproject.toml README.md ./
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy the runner script
COPY railway/run.py .

# Default command for cron execution
CMD ["python", "run.py", "daily"]
