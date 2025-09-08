#!/bin/sh
set -e

echo "===> Esperando a la DB..."
# Intenta conectar y migrar un par de veces por si la DB tarda en subir
for i in 1 2 3 4 5; do
  if flask db upgrade; then
    echo "===> Migraciones aplicadas."
    break
  fi
  echo "Migraciones fallaron, reintentando en 5s..."
  sleep 5
done

# Arrancar gunicorn en el puerto que Render expone en $PORT
exec gunicorn -w ${WEB_CONCURRENCY:-2} -k gthread --threads ${THREADS:-4} \
  -b 0.0.0.0:${PORT:-8000} manage:app
