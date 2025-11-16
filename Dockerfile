# Multi-stage build for WolfTrace
FROM oven/bun:1-alpine AS frontend-builder
WORKDIR /app/frontend
# Copy package.json first for better layer caching
COPY frontend/package.json ./
# Copy rest of frontend files (including bun.lockb if it exists)
COPY frontend/ ./
# Install dependencies (use frozen lockfile if available, otherwise regular install)
RUN if [ -f bun.lockb ]; then bun install --frozen-lockfile; else bun install; fi
# Build the frontend (a11y warnings are non-blocking)
RUN bun run build || (echo "Build failed, check errors above" && exit 1)

FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Copy plugins and config
COPY plugins/ ./plugins/
COPY config/ ./config/

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 5000

# Set environment
ENV FLASK_APP=backend/app.py
ENV PYTHONPATH=/app

# Run backend (you may want to serve frontend via Flask or nginx)
CMD ["python", "backend/app.py"]

