FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
# Sin privilegios de administrador dentro del contenedor
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "./arrancar.sh"]
