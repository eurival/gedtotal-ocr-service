FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    git \
    ghostscript \
    libleptonica-dev \
    pngquant \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-por \
    unpaper \
    && git clone --depth 1 https://github.com/agl/jbig2enc.git /tmp/jbig2enc \
    && cmake -S /tmp/jbig2enc -B /tmp/jbig2enc/build \
    && cmake --build /tmp/jbig2enc/build --parallel \
    && cmake --install /tmp/jbig2enc/build \
    && rm -rf /tmp/jbig2enc \
    && apt-get purge -y --auto-remove \
        build-essential \
        cmake \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8093

CMD ["python", "-m", "app.main"]
