# webhook/Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Copy dependency file from the root
COPY pyproject.toml .

# Install dependencies using uv
RUN pip install uv && uv pip install --system .

# Copy only the webhook code (and optionally shared code like flows)
COPY webhook/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
