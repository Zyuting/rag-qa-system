# Stage 1: Backend
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system deps for faiss, sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY knowledge_bases/ knowledge_bases/
COPY pyproject.toml .

EXPOSE 8001

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
