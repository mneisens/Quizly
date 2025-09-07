# Quizly Backend


### Voraussetzungen
- Python 3.8+
- pip
- **ffmpeg** (für YouTube-Video-Verarbeitung)

### ffmpeg Installation

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
1. Download von https://ffmpeg.org/download.html
2. Entpacken und zu PATH hinzufügen
3. Oder mit Chocolatey: `choco install ffmpeg`

**Überprüfung:**
```bash
ffmpeg -version
```

### Installation

1. **Repository klonen**
```bash
git clone https://github.com/mneisens/Quizly.git
cd Quizly
```

2. **Virtuelle Umgebung erstellen**
```bash
python3 -m venv env
source env/bin/activate  # macOS/Linux
# env\Scripts\activate   # Windows
```

3. **Abhängigkeiten installieren**
```bash
pip install -r requirements.txt
```

4. **Datenbank einrichten**
```bash
python manage.py migrate
```

5. **Server starten**
```bash
python manage.py runserver
```

Der Server läuft dann unter: `http://localhost:8000`

## API Endpunkte

- **Admin:** `http://localhost:8000/admin/`
- **API Base:** `http://localhost:8000/api/`
- **Dokumentation:** Siehe separate API-Dokumentation


## Support

Bei Problemen:
1. Logs prüfen
2. Django Debug-Toolbar verwenden
3. Issue im Repository erstellen