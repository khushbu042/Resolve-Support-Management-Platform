# Development Dockerfile - optimized for hot reload and fast iteration
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*


# Install uv (faster package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configure uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock .

# Install dependencies without installing the project itself
RUN uv sync --locked --no-install-project

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with hot reload for development
CMD ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
