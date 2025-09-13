# 🐳 Docker Setup Guide für Quizly Backend

## 🚀 Super einfacher Start

**Für deine Kollegen - nur 3 Schritte:**

### 1. Docker installieren
- **macOS:** https://www.docker.com/products/docker-desktop
- **Windows:** https://www.docker.com/products/docker-desktop
- **Linux:** `sudo apt install docker.io docker-compose`

### 2. Projekt starten
```bash
git clone <repository-url>
cd Quizly_Backend
docker-compose up
```

### 3. Fertig!
- Server läuft auf: `http://localhost:8000`
- API: `http://localhost:8000/api/`

## ✅ Was Docker automatisch macht

- ✅ **FFmpeg installiert** (keine manuelle Installation nötig)
- ✅ **Python-Zertifikate konfiguriert** (keine SSL-Fehler)
- ✅ **Whisper-Modell heruntergeladen** (keine Download-Fehler)
- ✅ **Alle Dependencies installiert** (requirements.txt)
- ✅ **Datenbank migriert** (automatisch beim Start)
- ✅ **Konsistente Umgebung** (funktioniert auf allen Systemen)

## 🔧 Docker-Befehle

### Container starten
```bash
docker-compose up
```

### Container im Hintergrund starten
```bash
docker-compose up -d
```

### Container stoppen
```bash
docker-compose down
```

### Logs anzeigen
```bash
docker-compose logs -f
```

### Container neu bauen (nach Code-Änderungen)
```bash
docker-compose up --build
```

### In Container einsteigen (für Debugging)
```bash
docker-compose exec quizly-backend bash
```

## 🗂️ Dateien erklärt

### `Dockerfile`
- Basis-Image: Python 3.11
- FFmpeg installiert
- SSL-Zertifikate konfiguriert
- Whisper-Modell vorab heruntergeladen
- Django-Server startet automatisch

### `docker-compose.yml`
- Port 8000 freigegeben
- Datenbank persistent gespeichert
- Health-Check für Container-Status
- Automatischer Neustart bei Fehlern

### `.dockerignore`
- Optimiert Build-Performance
- Schließt unnötige Dateien aus

## 🚨 Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
docker-compose logs

# Container neu bauen
docker-compose up --build
```

### Port bereits belegt
```bash
# Anderen Port verwenden
docker-compose up -p 8001:8000
```

### Datenbank-Reset
```bash
# Container stoppen und Datenbank löschen
docker-compose down
rm db.sqlite3
docker-compose up
```

### Container komplett zurücksetzen
```bash
# Alles löschen und neu starten
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## 📊 Vorteile für dein Team

### Für Kollegen:
- **Keine Setup-Probleme** mehr
- **Ein Befehl** startet alles
- **Funktioniert überall** (macOS, Windows, Linux)
- **Keine SSL-Fehler** oder FFmpeg-Probleme

### Für dich:
- **Weniger Support** nötig
- **Konsistente Umgebung** für alle
- **Einfaches Deployment**
- **Reproduzierbare Tests**

## 🎯 Vergleich: Mit vs. Ohne Docker

### Ohne Docker (vorher):
- FFmpeg installieren
- Python-Zertifikate fixen
- Whisper-Modell herunterladen
- SSL-Probleme lösen
- PATH-Probleme
- **→ 20+ Schritte, viele Fehlerquellen**

### Mit Docker (jetzt):
- Docker installieren
- `docker-compose up`
- **→ 2 Schritte, funktioniert immer**

## 🚀 Ready to go!

Deine Kollegen brauchen jetzt nur noch:
1. Docker installieren
2. `docker-compose up` ausführen

**Keine FFmpeg-Installation, keine SSL-Probleme, keine Setup-Guides mehr!**
