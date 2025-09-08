# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=manage.py \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    # ruta por defecto para uploads (la sobreescribimos en Render con un Disk)
    UPLOAD_FOLDER=/data/uploads

WORKDIR /app

# Dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Instala deps de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia proyecto
COPY . .

# Crea carpetas necesarias
RUN mkdir -p /app/instance "$UPLOAD_FOLDER"

# Script de arranque: migra y levanta gunicorn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
CMD ["sh", "-c", "/entrypoint.sh"]
