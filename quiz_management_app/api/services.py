import os
import tempfile
import json
import re
import whisper
import yt_dlp
from django.conf import settings

class QuizGenerationService:
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        try:
            self.whisper_model = whisper.load_model("base")
        except Exception:
            pass
    
    def _create_temp_directory(self):
        return tempfile.mkdtemp()
    
    def _download_youtube_audio(self, youtube_url, temp_dir):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_title = info.get('title', 'Unknown Video')
            
            mp3_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
            if mp3_files:
                mp3_path = os.path.join(temp_dir, mp3_files[0])
                return mp3_path, video_title
            else:
                raise Exception("MP3-Datei nicht gefunden")
                
        except Exception as e:
            raise Exception(f"Fehler beim Herunterladen: {str(e)}")
    
    def _transcribe_audio(self, audio_path):
        try:
            result = self.whisper_model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            raise Exception(f"Fehler bei der Transkription: {str(e)}")
    
    def _generate_quiz_with_gemini(self, video_title, transcript):
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Erstelle ein Quiz basierend auf dem folgenden Transkript eines YouTube-Videos.
            
            Video-Titel: {video_title}
            
            Transkript:
            {transcript}
            
            Erstelle 5 Multiple-Choice-Fragen mit jeweils 4 Antwortoptionen (A, B, C, D).
            Nur eine Antwort sollte korrekt sein.
            
            WICHTIGE REGELN FÜR ANTWORTMÖGLICHKEITEN:
            1. Alle Antwortmöglichkeiten müssen aus dem Video-Inhalt stammen
            2. Die falschen Antworten sollten plausibel sein, aber eindeutig falsch
            3. Verwende spezifische Begriffe, Namen, Zahlen oder Fakten aus dem Transkript
            4. Die Antworten sollten verschiedene Aspekte des Videos abdecken
            5. Vermeide zu offensichtliche oder zu schwierige Fragen
            6. Erstelle realistische Ablenkungen basierend auf dem Video-Inhalt
            
            BEISPIELE FÜR GUTE ANTWORTMÖGLICHKEITEN:
            - Wenn das Video über Zeitreisen spricht: ["Zeitreisen", "Raumfahrt", "Geschichte", "Fiktion"]
            - Wenn das Video über Sterne spricht: ["Weiße Zwerge", "Rote Riesen", "Schwarze Löcher", "Planeten"]
            - Wenn das Video über Technologie spricht: ["Künstliche Intelligenz", "Roboter", "Computer", "Smartphones"]
            
            Gib die Antworten im folgenden JSON-Format zurück:
            {{
                "title": "Quiz-Titel basierend auf dem Video",
                "description": "Kurze Beschreibung des Quiz",
                "questions": [
                    {{
                        "question_title": "Frage 1",
                        "question_options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer": "Option A"
                    }},
                    ...
                ]
            }}
            
            WICHTIG: Alle Antwortmöglichkeiten müssen spezifisch zum Video-Inhalt passen!
            Verwende Begriffe, Namen, Zahlen oder Fakten, die tatsächlich im Transkript erwähnt werden.
            """
            
            response = model.generate_content(prompt)
            return self._extract_json_from_response(response.text)
            
        except Exception as e:
            raise Exception(f"Fehler bei der Quiz-Generierung: {str(e)}")
    
    def _generate_test_quiz(self, video_title, transcript):
        words = transcript.split()[:20]
        sample_text = " ".join(words)
        
        if "Zeitreisen" in video_title or "time travel" in video_title.lower():
            theme_options = ["Zeitreisen", "Raumfahrt", "Geschichte", "Fiktion"]
            video_type = "Wissenschaftsdokumentation"
            content_sample = "Zeitreisen und ihre wissenschaftlichen Grundlagen"
        elif "Zwerge" in video_title or "dwarf" in video_title.lower():
            theme_options = ["Astronomie", "Sterne", "Physik", "Kosmologie"]
            video_type = "Wissenschaftsdokumentation"
            content_sample = "Weiße Zwerge und schwarze Zwerge im Universum"
        elif "Menschheit" in video_title or "humanity" in video_title.lower():
            theme_options = ["Menschheit", "Überleben", "Zukunft", "Evolution"]
            video_type = "Wissenschaftsdokumentation"
            content_sample = "Das Überleben der Menschheit im Universum"
        elif "Tutorial" in video_title.lower() or "how to" in video_title.lower():
            theme_options = ["Anleitung", "Lernen", "Technik", "Bildung"]
            video_type = "Tutorial"
            content_sample = "Schritt-für-Schritt-Anleitung"
        elif "Gaming" in video_title.lower() or "game" in video_title.lower():
            theme_options = ["Gaming", "Spiele", "Entertainment", "Freizeit"]
            video_type = "Gaming-Video"
            content_sample = "Spielvorstellung und Gameplay"
        elif "Musik" in video_title.lower() or "song" in video_title.lower():
            theme_options = ["Musik", "Kunst", "Kultur", "Entertainment"]
            video_type = "Musikvideo"
            content_sample = "Musikalische Darbietung"
        elif "News" in video_title.lower() or "Nachrichten" in video_title:
            theme_options = ["Nachrichten", "Aktualität", "Information", "Journalismus"]
            video_type = "Nachrichten"
            content_sample = "Aktuelle Ereignisse und Berichte"
        else:
            common_words = [word.lower() for word in transcript.split() if len(word) > 3]
            word_freq = {}
            for word in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            relevant_words = [word for word, freq in sorted_words[:10] if word not in ['das', 'die', 'der', 'und', 'ist', 'ein', 'eine', 'den', 'von', 'mit', 'für', 'auf', 'an', 'in', 'zu', 'bei', 'seit', 'aus', 'nach', 'über', 'unter', 'zwischen', 'durch', 'ohne', 'gegen', 'um', 'vor', 'hinter', 'neben', 'innerhalb', 'außerhalb']]
            
            if len(relevant_words) >= 3:
                theme_options = [relevant_words[0].title(), relevant_words[1].title(), relevant_words[2].title(), "Anderes Thema"]
            else:
                theme_options = ["Wissenschaft", "Technologie", "Bildung", "Forschung"]
            
            video_type = "Dokumentation"
            content_sample = sample_text[:50] + "..."
        
        return {
            "title": f"Quiz: {video_title}",
            "description": f"Ein Quiz basierend auf dem Video '{video_title}'",
            "questions": [
                {
                    "question_title": f"Was ist das Hauptthema des Videos '{video_title}'?",
                    "question_options": theme_options,
                    "answer": theme_options[0]
                },
                {
                    "question_title": "Wie viele Wörter enthält das Transkript?",
                    "question_options": [
                        f"{len(transcript.split())}",
                        f"{len(transcript.split()) + 50}",
                        f"{len(transcript.split()) - 50}", 
                        f"{len(transcript.split()) + 100}"
                    ],
                    "answer": f"{len(transcript.split())}"
                },
                {
                    "question_title": "Welche Art von Video ist das?",
                    "question_options": [
                        video_type,
                        "Entertainment",
                        "Nachrichten",
                        "Werbung"
                    ],
                    "answer": video_type
                },
                {
                    "question_title": "Was wird im Video hauptsächlich besprochen?",
                    "question_options": [
                        content_sample,
                        "Ein anderes Thema",
                        "Nichts Relevantes",
                        "Etwas anderes"
                    ],
                    "answer": content_sample
                },
                {
                    "question_title": "Wie lang ist das Transkript?",
                    "question_options": [
                        f"{len(transcript)} Zeichen",
                        f"{len(transcript) + 1000} Zeichen",
                        f"{len(transcript) - 1000} Zeichen",
                        f"{len(transcript) + 500} Zeichen"
                    ],
                    "answer": f"{len(transcript)} Zeichen"
                }
            ]
        }
    
    def _extract_json_from_response(self, response_text):
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                raise Exception("Kein JSON in der Antwort gefunden")
        except Exception as e:
            raise Exception(f"Fehler beim Parsen der JSON-Antwort: {str(e)}")
    
    def _cleanup_temp_files(self, temp_dir):
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    
    def generate_quiz_from_youtube(self, youtube_url):
        temp_dir = None
        try:
            temp_dir = self._create_temp_directory()
            audio_path, video_title = self._download_youtube_audio(youtube_url, temp_dir)
            transcript = self._transcribe_audio(audio_path)
            
            if self.gemini_api_key:
                quiz_data = self._generate_quiz_with_gemini(video_title, transcript)
            else:
                quiz_data = self._generate_test_quiz(video_title, transcript)
            
            return quiz_data
            
        except Exception as e:
            raise Exception(f"Fehler in generate_quiz_from_youtube: {str(e)}")
        finally:
            if temp_dir:
                self._cleanup_temp_files(temp_dir)
