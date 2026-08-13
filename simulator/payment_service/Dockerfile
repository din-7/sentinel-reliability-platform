FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app_factory.py .
COPY payment_service ./payment_service

EXPOSE 8002

CMD ["uvicorn", "payment_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
