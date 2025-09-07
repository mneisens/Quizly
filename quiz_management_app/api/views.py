from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import (
    CreateQuizSerializer, QuizSerializer, QuizDetailSerializer,
    QuizPlaySerializer, SubmitAnswerSerializer, QuizEvaluationSerializer
)
from .services import QuizGenerationService
from .quiz_utils import (
    validate_youtube_url, get_youtube_url_from_data, create_error_response,
    get_authenticated_user, get_quiz_by_id, get_question_by_id,
    get_selected_option, get_or_create_quiz_session, get_quiz_session_by_id,
    get_completed_quiz_session, save_quiz_answer, move_to_next_question
)
from ..models import Quiz, Question, QuestionOption, QuizSession, QuizAnswer


class CreateQuizView(CreateAPIView):
    """View for creating quizzes from YouTube URLs"""
    serializer_class = CreateQuizSerializer
    permission_classes = [IsAuthenticated] 
    
    
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
            url = get_youtube_url_from_data(request.data)
            if not url:
                return create_error_response(
                    "YouTube-URL ist erforderlich.",
                    request.data
                )
            
            if not validate_youtube_url(url):
                return create_error_response(
                    "Ungültige YouTube-URL.",
                    {"received_url": url}
                )
            
            quiz_service = QuizGenerationService()
            quiz_data = quiz_service.generate_quiz_from_youtube(url)
            
            user = get_authenticated_user(request)
            quiz = self._create_quiz_from_data(quiz_data, url, user)
            self._create_questions_for_quiz(quiz, quiz_data['questions'])
            
            serializer = QuizDetailSerializer(quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return create_error_response(
                f"Fehler bei der Quiz-Generierung: {str(e)}",
                request.data,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuizListView(ListAPIView):
    """View for listing all quizzes"""
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated] 
    
    def get_queryset(self):
        """Returns quizzes for authenticated user"""
        return Quiz.objects.filter(created_by=self.request.user)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """View for quiz detail, update and delete operations"""
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Returns quizzes for authenticated user"""
        return Quiz.objects.filter(created_by=self.request.user)
    
    def get_object(self):
        """Gets quiz object with better error handling for null IDs"""
        try:
            pk = self.kwargs.get('pk')
            if pk is None or pk == 'null' or pk == '' or str(pk).lower() == 'null':
                return None
            return super().get_object()
        except Exception:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        """Handles quiz retrieval with better error messages"""
        obj = self.get_object()
        if obj is None:
            return Response(
                {"detail": "Quiz nicht gefunden oder ungültige ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Handles quiz update with better error messages"""
        obj = self.get_object()
        if obj is None:
            return Response(
                {"detail": "Quiz nicht gefunden oder ungültige ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Handles quiz deletion with better error messages"""
        obj = self.get_object()
        if obj is None:
            return Response(
                {"detail": "Quiz nicht gefunden oder ungültige ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        return super().destroy(request, *args, **kwargs)


class StartQuizView(GenericAPIView):
    """View for starting a quiz session"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, quiz_id):
        """Starts a new quiz session"""
        if quiz_id is None or quiz_id == 'null' or quiz_id == '' or str(quiz_id).lower() == 'null':
            return Response(
                {"detail": "Ungültige Quiz-ID."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quiz = get_quiz_by_id(quiz_id, request.user)
        if not quiz:
            return Response(
                {"detail": "Quiz nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        session = get_or_create_quiz_session(quiz, request.user)
        serializer = QuizPlaySerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitAnswerView(GenericAPIView):
    """View for submitting quiz answers"""
    permission_classes = [IsAuthenticated]
    serializer_class = SubmitAnswerSerializer
    
    def post(self, request, session_id):
        """Submits an answer and moves to next question"""
        session = get_quiz_session_by_id(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Quiz-Session nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if session.is_completed:
            return Response(
                {"detail": "Quiz bereits abgeschlossen."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        question = get_question_by_id(serializer.validated_data['question_id'])
        if not question:
            return Response(
                {"detail": "Frage nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        selected_option = get_selected_option(
            question, 
            serializer.validated_data['selected_option_text']
        )
        if not selected_option:
            return Response(
                {"detail": "Antwortoption nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        save_quiz_answer(session, question, selected_option)
        move_to_next_question(session)
        
        serializer = QuizPlaySerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizEvaluationView(GenericAPIView):
    """View for quiz evaluation results"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """Gets quiz evaluation results"""
        session = get_completed_quiz_session(session_id, request.user)
        if not session:
            return Response(
                {"detail": "Abgeschlossene Quiz-Session nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuizEvaluationSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

