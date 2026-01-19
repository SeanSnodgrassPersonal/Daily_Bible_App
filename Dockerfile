# syntax=docker/dockerfile:1

FROM python:3.12-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Gunicorn production server
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]
