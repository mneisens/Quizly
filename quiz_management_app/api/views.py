from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import CreateQuizSerializer, QuizSerializer, QuizDetailSerializer
from .services import QuizGenerationService
from ..models import Quiz, Question, QuestionOption


class CreateQuizView(CreateAPIView):
    """View for creating quizzes from YouTube URLs"""
    serializer_class = CreateQuizSerializer
    permission_classes = [AllowAny] 
    
    def _get_youtube_url(self, request_data):
        """Extracts YouTube URL from request data"""
        return request_data.get('youtube_url') or request_data.get('url')
    
    def _validate_youtube_url(self, url):
        """Validates if URL is a valid YouTube URL"""
        return 'youtube.com' in url or 'youtu.be' in url
    
    def _create_error_response(self, message, data=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Creates standardized error response"""
        response_data = {"detail": message}
        if data:
            response_data["received_data"] = data
        return Response(response_data, status=status_code)
    
    def _get_or_create_test_user(self):
        """Gets or creates a test user for quiz creation"""
        try:
            user = User.objects.first()
            if not user:
                user = self._create_test_user()
        except Exception:
            user = self._create_test_user()
        return user
    
    def _create_test_user(self):
        """Creates a test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_quiz_from_data(self, quiz_data, url, user):
        """Creates quiz object from quiz data"""
        return Quiz.objects.create(
            title=quiz_data['title'],
            description=quiz_data['description'],
            video_url=url,
            created_by=user
        )
    
    def _create_questions_for_quiz(self, quiz, questions_data):
        """Creates questions and options for quiz"""
        for question_data in questions_data:
            question = self._create_question(quiz, question_data)
            self._create_question_options(question, question_data)
    
    def _create_question(self, quiz, question_data):
        """Creates a single question"""
        return Question.objects.create(
            quiz=quiz,
            question_title=question_data['question_title']
        )
    
    def _create_question_options(self, question, question_data):
        """Creates options for a question"""
        for option_text in question_data['question_options']:
            is_correct = option_text == question_data['answer']
            QuestionOption.objects.create(
                question=question,
                option_text=option_text,
                is_correct=is_correct
            )
    
    def create(self, request, *args, **kwargs):
        """Handles quiz creation from YouTube URL"""
        try:
            url = self._get_youtube_url(request.data)
            if not url:
                return self._create_error_response(
                    "YouTube-URL ist erforderlich.",
                    request.data
                )
            
            if not self._validate_youtube_url(url):
                return self._create_error_response(
                    "Ungültige YouTube-URL.",
                    {"received_url": url}
                )
            
            quiz_service = QuizGenerationService()
            quiz_data = quiz_service.generate_quiz_from_youtube(url)
            
            user = self._get_or_create_test_user()
            quiz = self._create_quiz_from_data(quiz_data, url, user)
            self._create_questions_for_quiz(quiz, quiz_data['questions'])
            
            serializer = QuizDetailSerializer(quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return self._create_error_response(
                f"Fehler bei der Quiz-Generierung: {str(e)}",
                request.data,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuizListView(ListAPIView):
    """View for listing all quizzes"""
    serializer_class = QuizSerializer
    permission_classes = [AllowAny] 
    
    def get_queryset(self):
        """Returns all quizzes"""
        return Quiz.objects.all()


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """View for quiz detail, update and delete operations"""
    serializer_class = QuizDetailSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Returns all quizzes"""
        return Quiz.objects.all()

