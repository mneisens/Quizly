FROM python:3.11-slim

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python-Zertifikate und pip aktualisieren
RUN pip install --upgrade pip certifi

# SSL-Zertifikate für Python setzen
ENV SSL_CERT_FILE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem

# Arbeitsverzeichnis
WORKDIR /app

# Dependencies installieren
COPY requirements.txt .
RUN pip install -r requirements.txt

# Whisper-Modell vorab herunterladen (verhindert SSL-Fehler beim ersten Quiz)
RUN python -c "import whisper; whisper.load_model('tiny')"

# Code kopieren
COPY . .

# Datenbank-Ordner erstellen
RUN mkdir -p /app/data

# Port freigeben
EXPOSE 8000

# Datenbank migrieren und Server starten
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
