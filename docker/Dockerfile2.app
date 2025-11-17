
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    # 🩺 curl : nécessaire pour HEALTHCHECK (test endpoint /health)
    # Alternative : wget, mais curl plus standard pour API testing
    && rm -rf /var/lib/apt/lists/*
    # 🧹 NETTOYAGE : supprime cache apt (~100MB économisés)
    # /var/lib/apt/lists/ contient les métadonnées des packages
    # Bonne pratique : TOUJOURS nettoyer dans la même layer (optimisation taille)


COPY requirements/base.txt requirements/prod.txt requirements/monitoring.txt ./

RUN pip install --no-cache-dir \
    -r base.txt \
    -r prod.txt \
    -r monitoring.txt


COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/


EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "scripts/run_api.py"]

