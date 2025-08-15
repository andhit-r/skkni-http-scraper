# Base Python
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && python -m playwright install --with-deps

COPY app ./app

EXPOSE 8000
ENV TZ=Asia/Jakarta

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
