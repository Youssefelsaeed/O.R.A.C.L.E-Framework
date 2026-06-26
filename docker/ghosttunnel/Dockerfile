FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ghosttunnel.txt /app/
RUN pip install --no-cache-dir -r requirements-ghosttunnel.txt

COPY ghosttunnel /app/ghosttunnel
RUN mkdir -p /app/data /app/reports

EXPOSE 8004
CMD ["uvicorn", "ghosttunnel.main:app", "--host", "0.0.0.0", "--port", "8004"]
