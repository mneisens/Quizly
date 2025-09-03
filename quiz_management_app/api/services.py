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
            
            Erstelle GENAU 10 Multiple-Choice-Fragen mit jeweils 4 Antwortoptionen (A, B, C, D).
            Nur eine Antwort sollte korrekt sein.
            
            WICHTIGE REGELN FÜR ANTWORTMÖGLICHKEITEN:
            1. Alle Antwortmöglichkeiten müssen aus dem Video-Inhalt stammen
            2. Die falschen Antworten sollten plausibel sein, aber eindeutig falsch
            3. Verwende spezifische Begriffe, Namen, Zahlen oder Fakten aus dem Transkript
            4. Die Antworten sollten verschiedene Aspekte des Videos abdecken
            5. Vermeide zu offensichtliche oder zu schwierige Fragen
            6. Erstelle realistische Ablenkungen basierend auf dem Video-Inhalt
            7. Alle 10 Fragen müssen relevant zum Video-Inhalt sein
            8. Jede Frage muss genau 4 Antwortmöglichkeiten haben
            
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
                    {{
                        "question_title": "Frage 2",
                        "question_options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer": "Option B"
                    }},
                    ... (weitere 8 Fragen)
                ]
            }}
            
            WICHTIG: 
            - GENAU 10 Fragen erstellen
            - Jede Frage muss genau 4 Antwortmöglichkeiten haben
            - Alle Antwortmöglichkeiten müssen spezifisch zum Video-Inhalt passen!
            - Verwende Begriffe, Namen, Zahlen oder Fakten, die tatsächlich im Transkript erwähnt werden.
            """
            
            response = model.generate_content(prompt)
            return self._extract_json_from_response(response.text)
            
        except Exception as e:
            raise Exception(f"Fehler bei der Quiz-Generierung: {str(e)}")
    
    def _generate_test_quiz(self, video_title, transcript):
        # Fallback-Methode für den Fall, dass kein Gemini API-Key verfügbar ist
        # Generiert 10 Fragen basierend auf dem Transkript
        
        # Extrahiere relevante Wörter aus dem Transkript
        words = transcript.split()
        word_freq = {}
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if len(word_lower) > 3 and word_lower not in ['das', 'die', 'der', 'und', 'ist', 'ein', 'eine', 'den', 'von', 'mit', 'für', 'auf', 'an', 'in', 'zu', 'bei', 'seit', 'aus', 'nach', 'über', 'unter', 'zwischen', 'durch', 'ohne', 'gegen', 'um', 'vor', 'hinter', 'neben', 'innerhalb', 'außerhalb']:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Sortiere nach Häufigkeit und wähle die relevantesten Wörter
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        relevant_words = [word.title() for word, freq in sorted_words[:20]]
        
        # Erstelle 10 Fragen basierend auf dem Video-Inhalt
        questions = []
        
        # Frage 1: Hauptthema
        if len(relevant_words) >= 4:
            theme_options = [relevant_words[0], relevant_words[1], relevant_words[2], "Anderes Thema"]
        else:
            theme_options = ["Hauptthema", "Nebenthema", "Unterthema", "Anderes"]
        
        questions.append({
            "question_title": f"Was ist das Hauptthema des Videos '{video_title}'?",
            "question_options": theme_options,
            "answer": theme_options[0]
        })
        
        # Frage 2: Anzahl Wörter
        word_count = len(transcript.split())
        questions.append({
            "question_title": "Wie viele Wörter enthält das Transkript?",
            "question_options": [
                str(word_count),
                str(word_count + 50),
                str(word_count - 50), 
                str(word_count + 100)
            ],
            "answer": str(word_count)
        })
        
        # Frage 3: Video-Typ
        video_type = self._determine_video_type(video_title, transcript)
        questions.append({
            "question_title": "Welche Art von Video ist das?",
            "question_options": [
                video_type,
                "Entertainment",
                "Nachrichten",
                "Werbung"
            ],
            "answer": video_type
        })
        
        # Frage 4: Transkript-Länge
        char_count = len(transcript)
        questions.append({
            "question_title": "Wie lang ist das Transkript?",
            "question_options": [
                f"{char_count} Zeichen",
                f"{char_count + 1000} Zeichen",
                f"{char_count - 1000} Zeichen",
                f"{char_count + 500} Zeichen"
            ],
            "answer": f"{char_count} Zeichen"
        })
        
        # Frage 5: Häufigstes Wort
        if relevant_words:
            most_common = relevant_words[0]
            questions.append({
                "question_title": "Welches Wort kommt im Transkript am häufigsten vor?",
                "question_options": [
                    most_common,
                    relevant_words[1] if len(relevant_words) > 1 else "Wort B",
                    relevant_words[2] if len(relevant_words) > 2 else "Wort C",
                    relevant_words[3] if len(relevant_words) > 3 else "Wort D"
                ],
                "answer": most_common
            })
        else:
            questions.append({
                "question_title": "Wie viele verschiedene Wörter enthält das Transkript?",
                "question_options": [
                    str(len(set(words))),
                    str(len(set(words)) + 100),
                    str(len(set(words)) - 100),
                    str(len(set(words)) + 200)
                ],
                "answer": str(len(set(words)))
            })
        
        # Frage 6: Video-Dauer (geschätzt)
        estimated_duration = len(words) // 150  # Geschätzte Wörter pro Minute
        questions.append({
            "question_title": "Wie lang ist das Video ungefähr (basierend auf dem Transkript)?",
            "question_options": [
                f"{estimated_duration} Minuten",
                f"{estimated_duration + 2} Minuten",
                f"{estimated_duration - 2} Minuten",
                f"{estimated_duration + 5} Minuten"
            ],
            "answer": f"{estimated_duration} Minuten"
        })
        
        # Frage 7: Sprache
        german_words = len([w for w in words if any(c in w for c in 'äöüß')])
        if german_words > len(words) * 0.1:
            language = "Deutsch"
        else:
            language = "Englisch"
        
        questions.append({
            "question_title": "In welcher Sprache ist das Video hauptsächlich?",
            "question_options": [
                language,
                "Spanisch" if language != "Spanisch" else "Französisch",
                "Französisch" if language != "Französisch" else "Italienisch",
                "Italienisch" if language != "Italienisch" else "Deutsch"
            ],
            "answer": language
        })
        
        # Frage 8: Komplexität
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        if avg_word_length > 8:
            complexity = "Komplex"
        elif avg_word_length > 6:
            complexity = "Mittel"
        else:
            complexity = "Einfach"
        
        questions.append({
            "question_title": "Wie komplex ist die Sprache im Video?",
            "question_options": [
                complexity,
                "Sehr einfach",
                "Mittel",
                "Sehr komplex"
            ],
            "answer": complexity
        })
        
        # Frage 9: Themenvielfalt
        unique_topics = len(set(word.lower() for word in words if len(word) > 5))
        if unique_topics > 100:
            variety = "Hoch"
        elif unique_topics > 50:
            variety = "Mittel"
        else:
            variety = "Niedrig"
        
        questions.append({
            "question_title": "Wie vielfältig sind die Themen im Video?",
            "question_options": [
                variety,
                "Sehr niedrig",
                "Mittel",
                "Sehr hoch"
            ],
            "answer": variety
        })
        
        # Frage 10: Zusammenfassung
        sample_text = transcript[:100] + "..." if len(transcript) > 100 else transcript
        questions.append({
            "question_title": "Was wird im Video hauptsächlich besprochen?",
            "question_options": [
                sample_text,
                "Ein anderes Thema",
                "Nichts Relevantes",
                "Etwas anderes"
            ],
            "answer": sample_text
        })
        
        return {
            "title": f"Quiz: {video_title}",
            "description": f"Ein Quiz basierend auf dem Video '{video_title}'",
            "questions": questions
        }
    
    def _determine_video_type(self, video_title, transcript):
        """Bestimmt den Typ des Videos basierend auf Titel und Transkript"""
        title_lower = video_title.lower()
        transcript_lower = transcript.lower()
        
        if any(word in title_lower for word in ['tutorial', 'how to', 'anleitung', 'lernen']):
            return "Tutorial"
        elif any(word in title_lower for word in ['gaming', 'game', 'spiel', 'playthrough']):
            return "Gaming"
        elif any(word in title_lower for word in ['musik', 'song', 'music', 'lied']):
            return "Musikvideo"
        elif any(word in title_lower for word in ['news', 'nachrichten', 'bericht', 'report']):
            return "Nachrichten"
        elif any(word in title_lower for word in ['wissenschaft', 'science', 'forschung', 'research']):
            return "Wissenschaftsdokumentation"
        elif any(word in title_lower for word in ['comedy', 'humor', 'witzig', 'lustig']):
            return "Comedy"
        else:
            return "Dokumentation"
    
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
