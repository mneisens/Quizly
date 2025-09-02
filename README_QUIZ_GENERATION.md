# Quiz-Generierung mit YouTube, Whisper AI und Gemini Flash

## 🚀 Übersicht

Das Quizly Backend kann jetzt automatisch Quizzes aus YouTube-Videos generieren:

1. **YouTube-Download**: Lädt Audio von YouTube-Videos herunter
2. **Whisper AI**: Transkribiert die Audio-Datei
3. **Gemini Flash**: Generiert Quiz-Fragen basierend auf dem Transkript

## 📋 Voraussetzungen

### 1. FFmpeg installieren
```bash
# macOS (mit Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# Windows
# Download von https://ffmpeg.org/download.html
```

### 2. Python-Pakete installieren
```bash
# Virtuelle Umgebung aktivieren
source env/bin/activate

# Pakete installieren
pip install -r requirements.txt
```

### 3. Gemini API Key konfigurieren

1. Gehen Sie zu [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Erstellen Sie einen API Key
3. Setzen Sie die Umgebungsvariable:

```bash
# macOS/Linux
export GEMINI_API_KEY="ihr-api-key-hier"

# Windows
set GEMINI_API_KEY=ihr-api-key-hier
```

Oder erstellen Sie eine `.env` Datei:
```env
GEMINI_API_KEY=ihr-api-key-hier
```

## 🔧 Installation

### Schritt 1: FFmpeg installieren
```bash
brew install ffmpeg
```

### Schritt 2: Python-Pakete installieren
```bash
source env/bin/activate
pip install yt-dlp==2025.07.21 openai-whisper==20250625 google-generativeai==0.8.3 pydub==0.25.1
```

### Schritt 3: Gemini API Key setzen
```bash
export GEMINI_API_KEY="ihr-api-key-hier"
```

### Schritt 4: Django Server starten
```bash
python manage.py runserver 8000
```

## 📡 API Verwendung

### Quiz aus YouTube-Video erstellen

**Endpoint:** `POST /api/createQuiz/`

**Request Body:**
```json
{
    "url": "https://www.youtube.com/watch?v=example"
}
```

**Response:**
```json
{
    "id": 1,
    "title": "Quiz-Titel",
    "description": "Quiz-Beschreibung",
    "video_url": "https://www.youtube.com/watch?v=example",
    "questions": [
        {
            "id": 1,
            "question_title": "Frage 1",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A"
        }
    ]
}
```

## 🔍 Funktionsweise

### 1. YouTube-Download
- Verwendet `yt-dlp` für zuverlässige Downloads
- Extrahiert Audio im MP3-Format
- Unterstützt verschiedene YouTube-Formate

### 2. Audio-Transkription
- Verwendet OpenAI Whisper (lokal)
- Unterstützt mehrere Sprachen
- Hohe Transkriptionsgenauigkeit

### 3. Quiz-Generierung
- Verwendet Google Gemini Flash (kostenlos)
- Generiert 5 Multiple-Choice-Fragen
- Basierend auf dem Video-Transkript

## ⚠️ Wichtige Hinweise

1. **API Key**: Der Gemini API Key ist erforderlich
2. **Internet**: YouTube-Downloads benötigen Internetverbindung
3. **Speicher**: Temporäre Audio-Dateien werden automatisch gelöscht
4. **Länge**: Längere Videos benötigen mehr Zeit für Transkription

## 🐛 Fehlerbehebung

### "GEMINI_API_KEY nicht gesetzt"
```bash
export GEMINI_API_KEY="ihr-api-key-hier"
```

### "FFmpeg nicht gefunden"
```bash
brew install ffmpeg
```

### "Fehler beim YouTube-Download"
- Überprüfen Sie die YouTube-URL
- Stellen Sie sicher, dass das Video öffentlich ist

### "Fehler bei der Transkription"
- Überprüfen Sie die Audio-Qualität
- Längere Videos benötigen mehr Zeit

## 📝 Beispiel

```bash
# Quiz erstellen
curl -X POST http://localhost:8000/api/createQuiz/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## 🔄 Workflow

1. **Frontend** sendet YouTube-URL
2. **Backend** lädt Audio herunter
3. **Whisper** transkribiert Audio
4. **Gemini** generiert Quiz-Fragen
5. **Datenbank** speichert Quiz
6. **API** gibt Quiz zurück

## 📊 Performance

- **Download**: 1-5 Minuten (abhängig von Video-Länge)
- **Transkription**: 2-10 Minuten (abhängig von Audio-Länge)
- **Quiz-Generierung**: 5-15 Sekunden
- **Gesamt**: 3-15 Minuten pro Quiz
