import os
import tempfile
import json
import re
import time
import shutil
import whisper
import yt_dlp
import subprocess
import platform
from django.conf import settings

class QuizGenerationService:
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.whisper_model = None
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Checks if ffmpeg is available"""
        system = platform.system().lower()
        
        try:
            if system == 'windows':
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, check=True, timeout=5, shell=True)
            else:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            system_name = "Windows" if system == 'windows' else "macOS/Linux"
            raise Exception(
                f"ffmpeg ist nicht installiert oder nicht im PATH verfügbar ({system_name}). "
                "Bitte installiere ffmpeg:\n"
                "• macOS: brew install ffmpeg\n"
                "• Ubuntu/Debian: sudo apt install ffmpeg\n"
                "• Windows: https://ffmpeg.org/download.html\n"
                "• Windows (Chocolatey): choco install ffmpeg\n"
                "• Windows (Scoop): scoop install ffmpeg"
            )
    
    def _get_ffmpeg_path(self):
        """Gets the path to ffmpeg binary"""
        system = platform.system().lower()
        
        try:
            if system == 'windows':
                result = subprocess.run(['where', 'ffmpeg'], 
                                      capture_output=True, text=True, check=True, shell=True)
                return result.stdout.strip().split('\n')[0]
            else:
                result = subprocess.run(['which', 'ffmpeg'], 
                                      capture_output=True, text=True, check=True)
                return result.stdout.strip()
        except subprocess.CalledProcessError:
            if system == 'windows':
                fallback_paths = [
                    'C:\\ffmpeg\\bin\\ffmpeg.exe',
                    'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
                    'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
                    'ffmpeg.exe' 
                ]
            else:
                fallback_paths = [
                    '/opt/homebrew/bin/ffmpeg',
                    '/usr/local/bin/ffmpeg',    
                    '/usr/bin/ffmpeg',          
                ]
            
            for path in fallback_paths:
                if os.path.exists(path):
                    return path
            
            return 'ffmpeg' if system != 'windows' else 'ffmpeg.exe' 
    
    def _create_temp_directory(self):
        """Creates a temporary directory for file operations"""
        return tempfile.mkdtemp()
    
    def _get_download_formats(self):
        """Returns list of download formats to try"""
        return [
            'worstaudio',
            'bestaudio[ext=m4a]',
            'bestaudio[ext=webm]',
            'bestaudio',
            'worst[ext=mp4]',
            'worst'
        ]
    
    def _create_ydl_options(self, format_choice, temp_dir):
        """Creates yt-dlp options for download"""
        ydl_opts = {
            'format': format_choice,
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 2,
            'fragment_retries': 2,
            'ffmpeg_location': self._get_ffmpeg_path(),
        }
        
        if 'audio' in format_choice:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }]
        
        return ydl_opts
    
    def _find_audio_files(self, temp_dir):
        """Finds audio files in temporary directory"""
        audio_extensions = ('.mp3', '.m4a', '.webm', '.ogg', '.wav', '.mp4')
        return [file for file in os.listdir(temp_dir) 
                if file.endswith(audio_extensions)]
    
    def _try_download_format(self, youtube_url, format_choice, temp_dir):
        """Attempts download with specific format"""
        try:
            ydl_opts = self._create_ydl_options(format_choice, temp_dir)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                if info is None:
                    return None, None
                
                video_title = info.get('title', 'Unknown Video')
                audio_files = self._find_audio_files(temp_dir)
                
                if audio_files:
                    audio_path = os.path.join(temp_dir, audio_files[0])
                    return audio_path, video_title
                
                return None, None
                
        except Exception as e:
            error_msg = str(e).lower()
            if 'ffmpeg' in error_msg or 'ffprobe' in error_msg:
                raise Exception("ffmpeg ist nicht installiert. Bitte installiere ffmpeg: https://ffmpeg.org/download.html")
            return None, None
    
    def _download_youtube_audio(self, youtube_url, temp_dir):
        """Robust YouTube download with multiple format fallbacks"""
        formats_to_try = self._get_download_formats()
        
        for format_choice in formats_to_try:
            audio_path, video_title = self._try_download_format(
                youtube_url, format_choice, temp_dir)
            
            if audio_path and video_title:
                return audio_path, video_title
        
        raise Exception("All download formats failed")
    
    def _validate_audio_file(self, audio_path):
        """Validates audio file exists and is not empty"""
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        
        if os.path.getsize(audio_path) == 0:
            raise Exception("Audio file is empty")
    
    def _load_whisper_model(self):
        """Loads Whisper model if not already loaded"""
        if not self.whisper_model:
            self.whisper_model = whisper.load_model("tiny")
    
    def _transcribe_audio(self, audio_path):
        """Simple audio transcription using Whisper"""
        try:
            self._validate_audio_file(audio_path)
            self._load_whisper_model()
            
            result = self.whisper_model.transcribe(
                audio_path,
                fp16=False,
                verbose=False,
                word_timestamps=False,
                language="de"
            )
            
            return result["text"].strip()
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def _is_dummy_api_key(self):
        """Checks if API key is dummy key"""
        return (not self.gemini_api_key or 
                self.gemini_api_key == "AIzaSyDummyKeyForTesting")
    
    def _create_gemini_prompt(self, video_title, transcript):
        """Creates prompt for Gemini AI"""
        return f"""
Create a quiz with 10 questions based on the following video transcript.

VIDEO TITLE: {video_title}

TRANSCRIPT:
{transcript}

TASK:
Create 10 diverse and challenging questions that directly relate to the video content. The questions should:

1. Be specific to the video content
2. Have different difficulty levels (easy to hard)
3. Use different question types (facts, comprehension, analysis)
4. Be interesting and educational

FORMAT:
Respond ONLY with a valid JSON object in the following structure:
{{
    "title": "Quiz: [Video Title]",
    "description": "A challenging quiz based on the video '[Video Title]'",
    "questions": [
        {{
            "question_title": "Here is the question",
            "question_options": [
                "Answer A",
                "Answer B", 
                "Answer C",
                "Answer D"
            ],
            "answer": "The correct answer"
        }}
    ]
}}

IMPORTANT:
- Create exactly 10 questions
- Each question must have 4 answer options
- Answers should be plausible and diverse
- Use only information from the transcript
- Respond ONLY with the JSON, no additional explanations
"""
    
    def _call_gemini_api(self, prompt):
        """Calls Gemini API with prompt"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    
    def _generate_quiz_with_gemini(self, video_title, transcript):
        """Intelligent quiz generation using Gemini AI"""
        try:
            if self._is_dummy_api_key():
                return self._generate_gemini_style_fallback(video_title, transcript)
            
            prompt = self._create_gemini_prompt(video_title, transcript)
            response_text = self._call_gemini_api(prompt)
            quiz_data = self._extract_json_from_response(response_text)
            
            if not self._validate_quiz_data(quiz_data):
                return self._generate_gemini_style_fallback(video_title, transcript)
            
            return quiz_data
            
        except Exception:
            return self._generate_gemini_style_fallback(video_title, transcript)
    
    def _extract_json_from_response(self, response_text):
        """Extracts JSON from Gemini response"""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                return json.loads(response_text)
                
        except Exception:
            raise Exception("Invalid Gemini response")
    
    def _validate_quiz_data(self, quiz_data):
        """Validates quiz data structure"""
        try:
            if not isinstance(quiz_data, dict):
                return False
            
            if 'questions' not in quiz_data:
                return False
            
            questions = quiz_data['questions']
            if not isinstance(questions, list) or len(questions) != 10:
                return False
            
            for question in questions:
                if not self._validate_question_structure(question):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_question_structure(self, question):
        """Validates individual question structure"""
        if not isinstance(question, dict):
            return False
        
        required_fields = ['question_title', 'question_options', 'answer']
        for field in required_fields:
            if field not in question:
                return False
        
        options = question['question_options']
        return (isinstance(options, list) and len(options) == 4)
    
    def _get_question_generators(self):
        """Returns list of question generator functions"""
        return [
            self._create_comprehension_question,
            self._create_analysis_question,
            self._create_application_question,
            self._create_evaluation_question,
            self._create_synthesis_question
        ]
    
    def _generate_gemini_style_fallback(self, video_title, transcript):
        """Generates Gemini-like intelligent questions without API"""
        try:
            analysis = self._analyze_transcript_intelligently(transcript)
            questions = []
            question_generators = self._get_question_generators()
            
            for i in range(10):
                generator = question_generators[i % len(question_generators)]
                question = generator(analysis, video_title, i+1)
                if question:
                    questions.append(question)
            
            return {
                'title': f'Quiz: {video_title}',
                'description': f'An intelligent quiz based on the video "{video_title}"',
                'questions': questions[:10]
            }
            
        except Exception:
            return self._generate_gemini_style_fallback(video_title, transcript)
    
    def _get_analysis_categories(self):
        """Returns analysis categories for transcript"""
        return {
            'main_topics': [],
            'key_arguments': [],
            'statistics': [],
            'comparisons': [],
            'conclusions': [],
            'examples': []
        }
    
    def _get_keyword_mappings(self):
        """Returns keyword mappings for transcript analysis"""
        return {
            'main_topics': ['haupt', 'wichtig', 'zentral', 'kern'],
            'key_arguments': ['argument', 'behaupt', 'sagt', 'meint', 'glaubt'],
            'statistics': r'\d+(?:\.\d+)?(?:%|prozent|jahre?|monate?|tage?)',
            'comparisons': ['vergleich', 'anders', 'ähnlich', 'mehr', 'weniger', 'besser', 'schlechter'],
            'conclusions': ['schluss', 'folgerung', 'fazit', 'zusammenfassung', 'daher', 'deshalb'],
            'examples': ['beispiel', 'etwa', 'zum beispiel', 'wie', 'etwa']
        }
    
    def _categorize_sentence(self, sentence, sentence_lower, analysis, mappings):
        """Categorizes sentence into analysis categories"""
        if any(word in sentence_lower for word in mappings['main_topics']):
            analysis['main_topics'].append(sentence)
        elif any(word in sentence_lower for word in mappings['key_arguments']):
            analysis['key_arguments'].append(sentence)
        elif re.search(mappings['statistics'], sentence_lower):
            analysis['statistics'].append(sentence)
        elif any(word in sentence_lower for word in mappings['comparisons']):
            analysis['comparisons'].append(sentence)
        elif any(word in sentence_lower for word in mappings['conclusions']):
            analysis['conclusions'].append(sentence)
        elif any(word in sentence_lower for word in mappings['examples']):
            analysis['examples'].append(sentence)
    
    def _analyze_transcript_intelligently(self, transcript):
        """Analyzes transcript intelligently for better questions"""
        analysis = self._get_analysis_categories()
        mappings = self._get_keyword_mappings()
        sentences = transcript.split('. ')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                sentence_lower = sentence.lower()
                self._categorize_sentence(sentence, sentence_lower, analysis, mappings)
        
        return analysis
    
    def _create_answer_preview(self, text, max_words=8):
        """Creates answer preview from text"""
        words = text.split()[:max_words]
        return ' '.join(words) + "..." if len(words) == max_words else text
    
    def _create_question_options(self, answer_preview, wrong_answers):
        """Creates question options list"""
        return [answer_preview] + wrong_answers
    
    def _create_comprehension_question(self, analysis, video_title, question_num):
        """Creates specific comprehension questions based on video content"""
        if not analysis['main_topics']:
            return None
        
        topic = analysis['main_topics'][0]
        answer_preview = self._create_answer_preview(topic)
        wrong_answers = [
            "Something else is said",
            "The topic is not mentioned",
            "There is no clear main topic"
        ]
        
        return {
            'question_title': "What is said about the main topic in this video?",
            'question_options': self._create_question_options(answer_preview, wrong_answers),
            'answer': answer_preview
        }
    
    def _create_analysis_question(self, analysis, video_title, question_num):
        """Creates specific analysis questions based on video content"""
        if not analysis['key_arguments']:
            return None
        
        argument = analysis['key_arguments'][0]
        answer_preview = self._create_answer_preview(argument)
        wrong_answers = [
            "A different argument is presented",
            "No argument is presented",
            "The argument is unclear"
        ]
        
        return {
            'question_title': "What is argued in this video?",
            'question_options': self._create_question_options(answer_preview, wrong_answers),
            'answer': answer_preview
        }
    
    def _create_application_question(self, analysis, video_title, question_num):
        """Creates specific application questions based on video content"""
        if not analysis['examples']:
            return None
        
        example = analysis['examples'][0]
        answer_preview = self._create_answer_preview(example)
        wrong_answers = [
            "A different example is mentioned",
            "No example is mentioned",
            "The example is unclear"
        ]
        
        return {
            'question_title': "What concrete example is mentioned in this video?",
            'question_options': self._create_question_options(answer_preview, wrong_answers),
            'answer': answer_preview
        }
    
    def _create_evaluation_question(self, analysis, video_title, question_num):
        """Creates specific evaluation questions based on video content"""
        if not analysis['conclusions']:
            return None
        
        conclusion = analysis['conclusions'][0]
        answer_preview = self._create_answer_preview(conclusion)
        wrong_answers = [
            "A different conclusion is drawn",
            "No conclusion is drawn",
            "The conclusion is unclear"
        ]
        
        return {
            'question_title': "What concrete conclusion is drawn in this video?",
            'question_options': self._create_question_options(answer_preview, wrong_answers),
            'answer': answer_preview
        }
    
    def _create_synthesis_question(self, analysis, video_title, question_num):
        """Creates specific synthesis questions based on video content"""
        if not analysis['comparisons']:
            return None
        
        comparison = analysis['comparisons'][0]
        answer_preview = self._create_answer_preview(comparison)
        wrong_answers = [
            "A different comparison is made",
            "No comparison is made",
            "The comparison is unclear"
        ]
        
        return {
            'question_title': "What concrete comparison is made in this video?",
            'question_options': self._create_question_options(answer_preview, wrong_answers),
            'answer': answer_preview
        }
    
    def _cleanup_temp_files(self, temp_dir):
        """Cleans up temporary files"""
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    
    def generate_quiz_from_youtube(self, youtube_url):
        """Main method for quiz generation"""
        temp_dir = None
        try:
            temp_dir = self._create_temp_directory()
            audio_path, video_title = self._download_youtube_audio(youtube_url, temp_dir)
            transcript = self._transcribe_audio(audio_path)
            quiz_data = self._generate_quiz_with_gemini(video_title, transcript)
            return quiz_data
            
        except Exception as e:
            raise Exception(f"Error in generate_quiz_from_youtube: {str(e)}")
        finally:
            if temp_dir:
                self._cleanup_temp_files(temp_dir)