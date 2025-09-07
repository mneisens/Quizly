# Quizly Backend

AI-powered quiz generation from YouTube videos using Django REST Framework.

## Prerequisites
- Python 3.8+
- pip
- **ffmpeg** (for YouTube video processing)

## ffmpeg Installation

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
1. Download from https://ffmpeg.org/download.html
2. Extract and add to PATH
3. Or with Chocolatey: `choco install ffmpeg`

**Verification:**
```bash
ffmpeg -version
```

## Installation

1. **Clone repository**
```bash
git clone https://github.com/mneisens/Quizly.git
cd Quizly
```

2. **Create virtual environment**
```bash
python3 -m venv env
source env/bin/activate  # macOS/Linux
# env\Scripts\activate   # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
python manage.py migrate
```

5. **Start server**
```bash
python manage.py runserver
```

The server will run at: `http://localhost:8000`

## API Endpoints

- **Admin:** `http://localhost:8000/admin/`
- **API Base:** `http://localhost:8000/api/`
- **Documentation:** See separate API documentation

## Features

- User authentication with JWT tokens
- YouTube video processing with yt-dlp
- AI-powered quiz generation using Gemini API
- Audio transcription with Whisper
- RESTful API with Django REST Framework

## Support

If you encounter issues:
1. Check logs
2. Use Django Debug Toolbar
3. Create an issue in the repository