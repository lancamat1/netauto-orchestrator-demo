FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install .

COPY flows/ flows/
COPY webhook/ webhook/

CMD ["uvicorn", "webhook.main:app", "--host", "0.0.0.0", "--port", "5000"]