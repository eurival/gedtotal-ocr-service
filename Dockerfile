FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf \
    automake \
    build-essential \
    ca-certificates \
    git \
    ghostscript \
    libleptonica-dev \
    libtool \
    pkg-config \
    pngquant \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-por \
    unpaper \
    && git clone --depth 1 https://github.com/agl/jbig2enc.git /tmp/jbig2enc \
    && cd /tmp/jbig2enc \
    && ./autogen.sh \
    && ./configure \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /tmp/jbig2enc \
    && apt-get purge -y --auto-remove \
        autoconf \
        automake \
        build-essential \
        git \
        libtool \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8093

CMD ["python", "-m", "app.main"]
