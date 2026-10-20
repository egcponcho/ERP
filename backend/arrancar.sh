#!/bin/sh
# Arranque del contenedor: migraciones, configuración base (opcional) y servidor.
set -e
alembic upgrade head
# CARGAR_CONFIG_BASE=1: agrega las unidades, estados y tipos sugeridos que falten
# (datos/base.json). No duplica ni pisa lo que ya existe.
if [ "${CARGAR_CONFIG_BASE:-0}" = "1" ]; then
  python -m app.modulos.productos.instalacion "${ORGANIZACION_POR_DEFECTO:-1}"
fi
# PORT lo define la plataforma (Render, Railway, Cloud Run); 8000 en local
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
