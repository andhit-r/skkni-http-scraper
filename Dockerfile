# Base Debian slim + Python 3.12
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependensi untuk Chromium & rendering headless yang stabil di Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    # lib dependensi chromium/headless
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 \
    libcairo2 libcups2 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 \
    libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxrandr2 libxshmfence1 \
    libxss1 libxtst6 \
    # font umum biar render teks stabil
    fontconfig fonts-noto fonts-dejavu-core \
    # chromium dari repo Debian
    chromium \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Buat user non-root & direktori data
RUN adduser --disabled-password --gecos "" appuser \
 && mkdir -p /data \
 && chown -R appuser:appuser /data /app

USER appuser

# Beritahu helper dimana chromium berada
ENV CHROMIUM_PATH=/usr/bin/chromium

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
