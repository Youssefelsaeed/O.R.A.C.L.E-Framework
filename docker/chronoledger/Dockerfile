FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-chronoledger.txt /app/
RUN pip install --no-cache-dir -r requirements-chronoledger.txt

COPY chronoledger /app/chronoledger
RUN mkdir -p /app/data /app/reports

EXPOSE 8003
CMD ["uvicorn", "chronoledger.main:app", "--host", "0.0.0.0", "--port", "8003"]
