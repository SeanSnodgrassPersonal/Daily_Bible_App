# syntax=docker/dockerfile:1

# Use a stable Python version that exists on Docker Hub.
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

WORKDIR /code

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Fly.io expects the app to listen on internal_port (8080 in fly.toml)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
