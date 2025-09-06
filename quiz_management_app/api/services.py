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
            print(f"DEBUG: Starte Download für URL: {youtube_url}")
            
            available_formats = self._get_available_formats(youtube_url)
            print(f"DEBUG: Verfügbare Audio-Formate: {len(available_formats)}")
            
            format_choices = [
                'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'bestaudio',
                'worstaudio',
            ]
            
            for format_choice in format_choices:
                try:
                    print(f"DEBUG: Versuche Format: {format_choice}")
                    ydl_opts = {
                        'format': format_choice,
                        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'noplaylist': True,
                        'extract_flat': False,
                        'ignoreerrors': True,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=True)
                        video_title = info.get('title', 'Unknown Video')

                    audio_files = []
                    for file in os.listdir(temp_dir):
                        if file.endswith(('.mp3', '.m4a', '.webm', '.ogg', '.wav')):
                            audio_files.append(file)
                    
                    if audio_files:
                        audio_path = os.path.join(temp_dir, audio_files[0])
                        print(f"DEBUG: Erfolgreich heruntergeladen: {audio_files[0]}")
                        return audio_path, video_title
                        
                except Exception as e:
                    print(f"DEBUG: Format {format_choice} fehlgeschlagen: {str(e)}")
                    continue
            
            return self._download_without_conversion(youtube_url, temp_dir)
                
        except Exception as e:
            print(f"DEBUG: Alle Download-Versuche fehlgeschlagen: {str(e)}")
            return self._download_with_fallback(youtube_url, temp_dir)
    
    def _download_without_conversion(self, youtube_url, temp_dir):
        """Download ohne Audio-Konvertierung"""
        try:
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_title = info.get('title', 'Unknown Video')
            
            for file in os.listdir(temp_dir):
                if not file.endswith('.part'):  
                    file_path = os.path.join(temp_dir, file)
                    return file_path, video_title
            
            raise Exception("Keine Audio-Datei gefunden")
            
        except Exception as e:
            raise Exception(f"Download ohne Konvertierung fehlgeschlagen: {str(e)}")
    
    def _download_with_fallback(self, youtube_url, temp_dir):
        """Fallback-Download mit verschiedenen Formaten"""
        fallback_formats = [
            'worstaudio',  
            'best[height<=480]',  
            'best',  
        ]
        
        for format_choice in fallback_formats:
            try:
                print(f"DEBUG: Versuche Format: {format_choice}")
                ydl_opts = {
                    'format': format_choice,
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'ignoreerrors': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_title = info.get('title', 'Unknown Video')
                
                # Suche nach heruntergeladenen Dateien
                for file in os.listdir(temp_dir):
                    if not file.endswith('.part'):
                        file_path = os.path.join(temp_dir, file)
                        print(f"DEBUG: Erfolgreich heruntergeladen: {file}")
                        return file_path, video_title
                        
            except Exception as e:
                print(f"DEBUG: Format {format_choice} fehlgeschlagen: {str(e)}")
                continue
        
        raise Exception("Alle Download-Versuche fehlgeschlagen")
    
    def _get_available_formats(self, youtube_url):
        """Hilfsmethode um verfügbare Formate zu prüfen"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                formats = info.get('formats', [])
                
                audio_formats = []
                for fmt in formats:
                    if fmt.get('acodec') != 'none':  # Hat Audio
                        audio_formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'acodec': fmt.get('acodec'),
                            'quality': fmt.get('quality'),
                        })
                
                return audio_formats
                
        except Exception as e:
            print(f"DEBUG: Fehler beim Abrufen der Formate: {str(e)}")
            return []
    
    def _transcribe_audio(self, audio_path):
        try:
            print(f"DEBUG: Transkribiere Audio-Datei: {audio_path}")
            print(f"DEBUG: Datei-Format: {os.path.splitext(audio_path)[1]}")
            
            if not os.path.exists(audio_path):
                raise Exception(f"Audio-Datei nicht gefunden: {audio_path}")
            
            file_size = os.path.getsize(audio_path)
            print(f"DEBUG: Dateigröße: {file_size} Bytes")
            
            if file_size == 0:
                raise Exception("Audio-Datei ist leer")
            
            result = self.whisper_model.transcribe(audio_path)
            transcript = result["text"]
            
            print(f"DEBUG: Transkript-Länge: {len(transcript)} Zeichen")
            return transcript
            
        except Exception as e:
            print(f"DEBUG: Transkriptions-Fehler: {str(e)}")
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
            quiz_data = self._extract_json_from_response(response.text)
            if len(quiz_data.get('questions', [])) != 10:
                raise Exception(f"Gemini API hat {len(quiz_data.get('questions', []))} Fragen generiert, aber 10 sind erforderlich!")
            
            return quiz_data
            
        except Exception as e:
            raise Exception(f"Fehler bei der Quiz-Generierung: {str(e)}")
    
    def _generate_test_quiz(self, video_title, transcript):
        sentences = self._split_into_sentences(transcript)
        key_terms = self._extract_key_terms(transcript)
        facts = self._extract_facts(sentences)
        
        questions = []
        
        main_topic = self._identify_main_topic(sentences, key_terms)
        questions.append(self._create_topic_question(main_topic, key_terms))
        
        if len(key_terms) >= 4:
            questions.append(self._create_key_term_question(key_terms))
        

        for i, fact in enumerate(facts[:4]):
            if fact:
                questions.append(self._create_fact_question(fact, key_terms))

        numbers = self._extract_numbers(transcript)
        if numbers:
            questions.append(self._create_number_question(numbers, transcript))
        
        questions.append(self._create_video_detail_question(video_title, transcript))
        
        questions.append(self._create_summary_question(transcript, key_terms))
        
        while len(questions) < 10:
            questions.append(self._create_generic_question(key_terms, len(questions) + 1))
        
        questions = questions[:10]
        
        if len(questions) != 10:
            raise Exception(f"Fehler: Es wurden {len(questions)} Fragen generiert, aber 10 sind erforderlich!")
        
        return {
            "title": f"Quiz: {video_title}",
            "description": f"Ein Quiz basierend auf dem Video '{video_title}'",
            "questions": questions
        }
    
    def _split_into_sentences(self, text):
        """Teilt Text in Sätze auf"""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_key_terms(self, text):
        """Extrahiert wichtige Begriffe aus dem Text"""
        import re
        words = re.findall(r'\b[A-Za-zäöüßÄÖÜ]{4,}\b', text.lower())
        
        stop_words = {
            'das', 'die', 'der', 'und', 'ist', 'ein', 'eine', 'den', 'von', 'mit', 'für', 'auf', 'an', 'in', 'zu', 'bei', 'seit', 'aus', 'nach', 'über', 'unter', 'zwischen', 'durch', 'ohne', 'gegen', 'um', 'vor', 'hinter', 'neben', 'innerhalb', 'außerhalb', 'dass', 'nicht', 'oder', 'aber', 'wenn', 'wie', 'was', 'wer', 'wo', 'warum', 'wann', 'alle', 'viele', 'mehr', 'sehr', 'auch', 'noch', 'nur', 'schon', 'immer', 'kann', 'muss', 'soll', 'will', 'haben', 'sein', 'werden', 'können', 'müssen', 'sollen', 'wollen', 'haben', 'sind', 'wird', 'kann', 'muss', 'soll', 'will'
        }
        
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word.title() for word, freq in sorted_words[:15]]
    
    def _extract_facts(self, sentences):
        """Extrahiert Fakten aus Sätzen"""
        facts = []
        for sentence in sentences:
            if len(sentence) > 20 and any(word in sentence.lower() for word in ['ist', 'sind', 'war', 'waren', 'hat', 'haben', 'kann', 'können', 'muss', 'müssen']):
                facts.append(sentence)
        return facts[:5]
    
    def _identify_main_topic(self, sentences, key_terms):
        """Identifiziert das Hauptthema des Videos"""
        if key_terms:
            return key_terms[0]
        return "Allgemeines Thema"
    
    def _extract_numbers(self, text):
        """Extrahiert Zahlen aus dem Text"""
        import re
        numbers = re.findall(r'\b\d+\b', text)
        return [int(n) for n in numbers if int(n) > 0]
    
    def _create_topic_question(self, main_topic, key_terms):
        """Erstellt eine Frage zum Hauptthema"""
        options = [main_topic]
        if len(key_terms) >= 3:
            options.extend(key_terms[1:3])
        else:
            options.extend(["Anderes Thema", "Unbekanntes Thema"])
        
        # Füge eine falsche Option hinzu
        options.append("Komplett anderes Thema")
        
        return {
            "question_title": "Was ist das Hauptthema dieses Videos?",
            "question_options": options[:4],
            "answer": main_topic
        }
    
    def _create_key_term_question(self, key_terms):
        """Erstellt eine Frage zu wichtigen Begriffen"""
        if len(key_terms) < 4:
            return self._create_generic_question(key_terms, 1)
        
        correct_term = key_terms[0]
        wrong_terms = key_terms[1:4]
        
        return {
            "question_title": f"Welcher Begriff wird im Video am häufigsten erwähnt?",
            "question_options": [correct_term] + wrong_terms,
            "answer": correct_term
        }
    
    def _create_fact_question(self, fact, key_terms):
        """Erstellt eine Frage basierend auf einem Fakt"""
        # Vereinfache den Fakt für die Frage
        fact_words = fact.split()[:8]  # Erste 8 Wörter
        question_text = " ".join(fact_words) + "..."
        
        options = [
            "Richtig",
            "Falsch", 
            "Teilweise richtig",
            "Nicht erwähnt"
        ]
        
        return {
            "question_title": f"Wird folgendes im Video erwähnt: '{question_text}'?",
            "question_options": options,
            "answer": "Richtig"
        }
    
    def _create_number_question(self, numbers, transcript):
        """Erstellt eine Frage zu Zahlen im Video"""
        if not numbers:
            return self._create_generic_question([], 1)
        
        correct_number = numbers[0]
        wrong_numbers = [correct_number + 1, correct_number - 1, correct_number + 10]
        
        return {
            "question_title": "Welche Zahl wird im Video erwähnt?",
            "question_options": [str(correct_number)] + [str(n) for n in wrong_numbers],
            "answer": str(correct_number)
        }
    
    def _create_video_detail_question(self, video_title, transcript):
        """Erstellt eine Frage zu Video-Details"""
        word_count = len(transcript.split())
        estimated_duration = word_count // 150  # Geschätzte Minuten
        
        options = [
            f"Etwa {estimated_duration} Minuten",
            f"Etwa {estimated_duration + 2} Minuten", 
            f"Etwa {estimated_duration - 2} Minuten",
            f"Etwa {estimated_duration + 5} Minuten"
        ]
        
        return {
            "question_title": "Wie lang ist das Video ungefähr?",
            "question_options": options,
            "answer": f"Etwa {estimated_duration} Minuten"
        }
    
    def _create_summary_question(self, transcript, key_terms):
        """Erstellt eine Zusammenfassungsfrage"""
        # Erste 50 Wörter als Zusammenfassung
        summary_words = transcript.split()[:50]
        summary = " ".join(summary_words) + "..."
        
        options = [
            summary,
            "Ein anderes Thema",
            "Nichts Relevantes", 
            "Etwas anderes"
        ]
        
        return {
            "question_title": "Was wird im Video hauptsächlich besprochen?",
            "question_options": options,
            "answer": summary
        }
    
    def _create_generic_question(self, key_terms, question_num):
        """Erstellt eine generische Frage als Fallback"""
        if key_terms:
            correct = key_terms[0] if key_terms else "Begriff A"
            wrong = key_terms[1:3] if len(key_terms) > 2 else ["Begriff B", "Begriff C"]
        else:
            correct = "Option A"
            wrong = ["Option B", "Option C"]
        
        options = [correct] + wrong + ["Andere Option"]
        
        return {
            "question_title": f"Frage {question_num}: Welche Option ist korrekt?",
            "question_options": options[:4],
            "answer": correct
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
            
            print(f"DEBUG: Video-Titel: {video_title}")
            print(f"DEBUG: Transkript-Länge: {len(transcript)} Zeichen")
            print(f"DEBUG: Gemini API-Key verfügbar: {bool(self.gemini_api_key)}")
            
            if self.gemini_api_key:
                print("DEBUG: Verwende Gemini API für Quiz-Generierung")
                quiz_data = self._generate_quiz_with_gemini(video_title, transcript)
            else:
                print("DEBUG: Verwende Fallback-Methode für Quiz-Generierung")
                quiz_data = self._generate_test_quiz(video_title, transcript)
            
            print(f"DEBUG: Generierte Fragen: {len(quiz_data.get('questions', []))}")
            return quiz_data
            
        except Exception as e:
            print(f"DEBUG: Fehler in generate_quiz_from_youtube: {str(e)}")
            raise Exception(f"Fehler in generate_quiz_from_youtube: {str(e)}")
        finally:
            if temp_dir:
                self._cleanup_temp_files(temp_dir)
