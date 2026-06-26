FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ethicq.txt /app/
RUN pip install --no-cache-dir -r requirements-ethicq.txt

COPY ethicq /app/ethicq

EXPOSE 8002
CMD ["uvicorn", "ethicq.main:app", "--host", "0.0.0.0", "--port", "8002"]
