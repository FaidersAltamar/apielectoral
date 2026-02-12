FROM python:3.11-slim

# Logs inmediatos en Docker (sin buffer)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Usuario no-root (seguridad)
RUN useradd -r -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "worker_registraduria.py"]
