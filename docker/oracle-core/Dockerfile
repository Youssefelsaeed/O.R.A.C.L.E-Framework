FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-oracle-core.txt /app/
RUN pip install --no-cache-dir -r requirements-oracle-core.txt

COPY oracle_core /app/oracle_core
COPY mutantshield /app/mutantshield
COPY scripts/run_mutantshield_evolution.py /app/scripts/run_mutantshield_evolution.py

RUN mkdir -p /app/reports /app/data /app/models_candidate /app/models_final

EXPOSE 8000
CMD ["uvicorn", "oracle_core.main:app", "--host", "0.0.0.0", "--port", "8000"]
