FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8008

CMD ["sh", "-c", "sleep 5 && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8008"]