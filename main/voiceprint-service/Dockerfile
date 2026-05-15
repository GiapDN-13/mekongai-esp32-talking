FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libsndfile1 \
        ffmpeg \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN mkdir -p /app/data/voiceprints /app/pretrained_models/ecapa

ENV VOICEPRINT_DATA_DIR=/app/data/voiceprints
ENV VOICEPRINT_MODEL_DIR=/app/pretrained_models/ecapa
ENV VOICEPRINT_PORT=8100
ENV VOICEPRINT_HOST=0.0.0.0

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/voiceprint/health?key=' + __import__('os').getenv('VOICEPRINT_API_KEY','voiceprint-secret-key'))" || exit 1

CMD ["python", "app.py"]
