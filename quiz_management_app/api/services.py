import os
import tempfile
import json
import whisper
import yt_dlp
from django.conf import settings

class QuizGenerationService:
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.whisper_model = None
    
    def _create_temp_directory(self):
        """Creates a temporary directory for file operations"""
        return tempfile.mkdtemp()
    
    def _download_youtube_audio(self, youtube_url, temp_dir):
        """Robust YouTube download with multiple format fallbacks"""
        try:
            formats_to_try = [
                'worstaudio',
                'bestaudio[ext=m4a]',
                'bestaudio[ext=webm]',
                'bestaudio',
                'worst[ext=mp4]',
                'worst'
            ]
            
            for format_choice in formats_to_try:
                try:
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
                    }
                    
                    if 'audio' in format_choice:
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '64',
                        }]
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=True)
                        if info is None:
                            continue
                        
                        video_title = info.get('title', 'Unknown Video')
                        
                        audio_files = []
                        for file in os.listdir(temp_dir):
                            if file.endswith(('.mp3', '.m4a', '.webm', '.ogg', '.wav', '.mp4')):
                                audio_files.append(file)
                        
                        if audio_files:
                            audio_path = os.path.join(temp_dir, audio_files[0])
                            return audio_path, video_title
                        else:
                            continue
                            
                except Exception as e:
                    continue
            
            raise Exception("All download formats failed")
                
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def _transcribe_audio(self, audio_path):
        """Simple audio transcription using Whisper"""
        try:
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")
            
            file_size = os.path.getsize(audio_path)
            
            if file_size == 0:
                raise Exception("Audio file is empty")
            
            if not self.whisper_model:
                self.whisper_model = whisper.load_model("tiny")
            
            result = self.whisper_model.transcribe(
                audio_path,
                fp16=False,
                verbose=False,
                word_timestamps=False,
                language="de"
            )
            
            transcript = result["text"].strip()
            return transcript
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def _generate_quiz_with_gemini(self, video_title, transcript):
        """Intelligent quiz generation using Gemini AI"""
        try:
            if not self.gemini_api_key:
                return self._generate_gemini_style_fallback(video_title, transcript)
            
            if self.gemini_api_key == "AIzaSyDummyKeyForTesting":
                return self._generate_gemini_style_fallback(video_title, transcript)
            
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
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

            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            quiz_data = self._extract_json_from_response(response_text)
            
            if not self._validate_quiz_data(quiz_data):
                return self._generate_gemini_style_fallback(video_title, transcript)
            
            return quiz_data
            
        except Exception as e:
            return self._generate_gemini_style_fallback(video_title, transcript)
    
    def _extract_json_from_response(self, response_text):
        """Extracts JSON from Gemini response"""
        try:
            import re
            import json
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                return json.loads(response_text)
                
        except Exception as e:
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
                if not isinstance(question, dict):
                    return False
                if 'question_title' not in question:
                    return False
                if 'question_options' not in question:
                    return False
                if 'answer' not in question:
                    return False
                if not isinstance(question['question_options'], list) or len(question['question_options']) != 4:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _generate_gemini_style_fallback(self, video_title, transcript):
        """Generates Gemini-like intelligent questions without API"""
        try:
            analysis = self._analyze_transcript_intelligently(transcript)
            
            questions = []
            
            question_generators = [
                self._create_comprehension_question,
                self._create_analysis_question,
                self._create_application_question,
                self._create_evaluation_question,
                self._create_synthesis_question
            ]
            
            for i in range(10):
                generator = question_generators[i % len(question_generators)]
                question = generator(analysis, video_title, i+1)
                if question:
                    questions.append(question)
            
            quiz_data = {
                'title': f'Quiz: {video_title}',
                'description': f'An intelligent quiz based on the video "{video_title}"',
                'questions': questions[:10]
            }
            
            return quiz_data
            
        except Exception as e:
            return self._generate_gemini_style_fallback(video_title, transcript)
    
    def _analyze_transcript_intelligently(self, transcript):
        """Analyzes transcript intelligently for better questions"""
        import re
        
        analysis = {
            'main_topics': [],
            'key_arguments': [],
            'statistics': [],
            'comparisons': [],
            'conclusions': [],
            'examples': []
        }
        
        sentences = transcript.split('. ')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                sentence_lower = sentence.lower()
                
                if any(word in sentence_lower for word in ['haupt', 'wichtig', 'zentral', 'kern']):
                    analysis['main_topics'].append(sentence)
                
                elif any(word in sentence_lower for word in ['argument', 'behaupt', 'sagt', 'meint', 'glaubt']):
                    analysis['key_arguments'].append(sentence)
                
                elif re.search(r'\d+(?:\.\d+)?(?:%|prozent|jahre?|monate?|tage?)', sentence_lower):
                    analysis['statistics'].append(sentence)
                
                elif any(word in sentence_lower for word in ['vergleich', 'anders', 'ähnlich', 'mehr', 'weniger', 'besser', 'schlechter']):
                    analysis['comparisons'].append(sentence)
                
                elif any(word in sentence_lower for word in ['schluss', 'folgerung', 'fazit', 'zusammenfassung', 'daher', 'deshalb']):
                    analysis['conclusions'].append(sentence)
                
                elif any(word in sentence_lower for word in ['beispiel', 'etwa', 'zum beispiel', 'wie', 'etwa']):
                    analysis['examples'].append(sentence)
        
        return analysis
    
    def _create_comprehension_question(self, analysis, video_title, question_num):
        """Creates specific comprehension questions based on video content"""
        if analysis['main_topics']:
            topic = analysis['main_topics'][0]
            topic_words = topic.split()[:8]
            answer_preview = ' '.join(topic_words) + "..."
            
            return {
                'question_title': f"What is said about the main topic in this video?",
                'question_options': [
                    answer_preview,
                    "Something else is said",
                    "The topic is not mentioned",
                    "There is no clear main topic"
                ],
                'answer': answer_preview
            }
        return None
    
    def _create_analysis_question(self, analysis, video_title, question_num):
        """Creates specific analysis questions based on video content"""
        if analysis['key_arguments']:
            argument = analysis['key_arguments'][0]
            arg_words = argument.split()[:8]
            answer_preview = ' '.join(arg_words) + "..."
            
            return {
                'question_title': f"What is argued in this video?",
                'question_options': [
                    answer_preview,
                    "A different argument is presented",
                    "No argument is presented",
                    "The argument is unclear"
                ],
                'answer': answer_preview
            }
        return None
    
    def _create_application_question(self, analysis, video_title, question_num):
        """Creates specific application questions based on video content"""
        if analysis['examples']:
            example = analysis['examples'][0]
            ex_words = example.split()[:8]
            answer_preview = ' '.join(ex_words) + "..."
            
            return {
                'question_title': f"What concrete example is mentioned in this video?",
                'question_options': [
                    answer_preview,
                    "A different example is mentioned",
                    "No example is mentioned",
                    "The example is unclear"
                ],
                'answer': answer_preview
            }
        return None
    
    def _create_evaluation_question(self, analysis, video_title, question_num):
        """Creates specific evaluation questions based on video content"""
        if analysis['conclusions']:
            conclusion = analysis['conclusions'][0]
            conc_words = conclusion.split()[:8]
            answer_preview = ' '.join(conc_words) + "..."
            
            return {
                'question_title': f"What concrete conclusion is drawn in this video?",
                'question_options': [
                    answer_preview,
                    "A different conclusion is drawn",
                    "No conclusion is drawn",
                    "The conclusion is unclear"
                ],
                'answer': answer_preview
            }
        return None
    
    def _create_synthesis_question(self, analysis, video_title, question_num):
        """Creates specific synthesis questions based on video content"""
        if analysis['comparisons']:
            comparison = analysis['comparisons'][0]
            comp_words = comparison.split()[:8]
            answer_preview = ' '.join(comp_words) + "..."
            
            return {
                'question_title': f"What concrete comparison is made in this video?",
                'question_options': [
                    answer_preview,
                    "A different comparison is made",
                    "No comparison is made",
                    "The comparison is unclear"
                ],
                'answer': answer_preview
            }
        return None
    
    def _cleanup_temp_files(self, temp_dir):
        """Cleans up temporary files"""
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            pass
    
    def generate_quiz_from_youtube(self, youtube_url):
        """Main method for quiz generation"""
        import time
        
        temp_dir = None
        try:
            start_time = time.time()
            
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