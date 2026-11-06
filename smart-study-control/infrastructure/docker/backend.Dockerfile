FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /service
COPY backend/requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
RUN useradd --uid 10001 --create-home study && mkdir -p /data/uploads && chown -R study:study /data
COPY --chown=study:study backend/ .
COPY --chown=study:study infrastructure/docker/api-entrypoint.sh /entrypoint.sh
USER study
EXPOSE 8000
ENTRYPOINT ["sh", "/entrypoint.sh"]
