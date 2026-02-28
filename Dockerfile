FROM python:3.11-slim

WORKDIR /app

# system deps (opencv + mysql safe)
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# project
COPY app ./app

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "2"]