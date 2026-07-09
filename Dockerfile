FROM python:3.12-slim

LABEL maintainer="Raj Baibhav"
LABEL project="Chaos Engineering Simulator"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

EXPOSE 8000

RUN useradd -m appuser
USER appuser

CMD ["python", "-m", "http.server", "8000"]
