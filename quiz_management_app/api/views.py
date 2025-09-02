from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import CreateQuizSerializer, QuizSerializer, QuizDetailSerializer
from .services import QuizGenerationService
from ..models import Quiz, Question, QuestionOption


class TestYouTubeURLView(CreateAPIView):
    """Test-View für YouTube-URL-Eingabe ohne Authentifizierung"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            url = request.data.get('youtube_url')
            if not url:
                return Response({
                    "detail": "YouTube-URL ist erforderlich.",
                    "received_data": request.data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'youtube.com' not in url and 'youtu.be' not in url:
                return Response({
                    "detail": "Ungültige YouTube-URL.",
                    "received_url": url
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "message": "YouTube-URL erfolgreich empfangen!",
                "youtube_url": url,
                "status": "URL validiert",
                "next_step": "Quiz-Generierung würde hier starten"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "detail": f"Fehler bei der URL-Verarbeitung: {str(e)}",
                "received_data": request.data
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateQuizView(CreateAPIView):
    serializer_class = CreateQuizSerializer
    permission_classes = [AllowAny] 
    
    def create(self, request, *args, **kwargs):
        try:
            url = request.data.get('youtube_url') or request.data.get('url')
            if not url:
                return Response({
                    "detail": "YouTube-URL ist erforderlich.",
                    "received_data": request.data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if 'youtube.com' not in url and 'youtu.be' not in url:
                return Response({
                    "detail": "Ungültige YouTube-URL.",
                    "received_url": url
                }, status=status.HTTP_400_BAD_REQUEST)
            
            quiz_service = QuizGenerationService()
            quiz_data = quiz_service.generate_quiz_from_youtube(url)
            
            from django.contrib.auth.models import User
            try:
                user = User.objects.first()
                if not user:
                    user = User.objects.create_user(
                        username='testuser',
                        email='test@example.com',
                        password='testpass123'
                    )
            except Exception:
                user = User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123'
                )
            
            quiz = Quiz.objects.create(
                title=quiz_data['title'],
                description=quiz_data['description'],
                video_url=url,
                created_by=user
            )
            
            for question_data in quiz_data['questions']:
                question = Question.objects.create(
                    quiz=quiz,
                    question_title=question_data['question_title']
                )
                
                for option_text in question_data['question_options']:
                    is_correct = option_text == question_data['answer']
                    QuestionOption.objects.create(
                        question=question,
                        option_text=option_text,
                        is_correct=is_correct
                    )
            
            serializer = QuizDetailSerializer(quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "detail": f"Fehler bei der Quiz-Generierung: {str(e)}",
                "received_data": request.data
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuizListView(ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [AllowAny] 
    
    def get_queryset(self):
        return Quiz.objects.all()


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = QuizDetailSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Quiz.objects.all()
