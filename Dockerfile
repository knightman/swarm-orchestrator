# --- Frontend build ---
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Python runtime ---
FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml ./
COPY backend/ ./backend/
RUN pip install --no-cache-dir .

COPY definitions/ ./definitions/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
