FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Force uv to install to the system Python and compile bytecode for performance
ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip install --no-cache -r pyproject.toml

# Copy application code
COPY . .

# Ensure the database file location is writable
RUN mkdir -p /app/data

EXPOSE 443
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]