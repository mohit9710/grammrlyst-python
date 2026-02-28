FROM python:3.11-slim

WORKDIR /app

# system deps (optional but good)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements copy
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# project copy
COPY app ./app

WORKDIR /app/app

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "2"]