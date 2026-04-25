FROM python:3.12-slim

LABEL org.opencontainers.image.title="ZM2_Mereni"
LABEL org.opencontainers.image.description="Statistické zpracování dat (Základy měření 2)"
LABEL org.opencontainers.image.source="https://github.com/matyas095/ZM2_Mereni"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py main_statistika.py main_grafy.py utils.py ./
COPY statisticke_vypracovani/ ./statisticke_vypracovani/
COPY objects/ ./objects/
COPY zm2/ ./zm2/

VOLUME ["/data"]
WORKDIR /data

ENTRYPOINT ["python3", "/app/main.py"]
CMD ["--help"]
