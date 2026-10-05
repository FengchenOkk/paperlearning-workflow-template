FROM node:22-alpine AS web
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /build/frontend/dist /app/frontend/dist
RUN useradd --create-home papergraph && mkdir -p /app/data/documents && chown -R papergraph:papergraph /app/data /app/backend
USER papergraph
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "papergraph.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
