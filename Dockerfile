FROM python:3.11-slim

WORKDIR /app

# Copy requirements dulu (biar cache optimal)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file project
COPY . .

# Set environment (optional tapi bagus)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "app.py"]