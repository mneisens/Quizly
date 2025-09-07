from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import User
from ..models import Quiz, Question, QuestionOption, QuizSession, QuizAnswer


def validate_youtube_url(url):
    """Validates if URL is a valid YouTube URL"""
    return 'youtube.com' in url or 'youtu.be' in url


def get_youtube_url_from_data(request_data):
    """Extracts YouTube URL from request data"""
    return request_data.get('youtube_url') or request_data.get('url')


def create_error_response(message, data=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Creates standardized error response"""
    response_data = {"detail": message}
    if data:
        response_data["received_data"] = data
    return Response(response_data, status=status_code)


def get_authenticated_user(request):
    """Gets the authenticated user from request"""
    return request.user


def get_quiz_by_id(quiz_id, user):
    """Gets quiz by ID for authenticated user"""
    try:
        return Quiz.objects.get(id=quiz_id, created_by=user)
    except Quiz.DoesNotExist:
        return None


def get_question_by_id(question_id):
    """Gets question by ID"""
    try:
        return Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return None


def get_selected_option(question, option_text):
    """Gets selected option by text"""
    try:
        return question.question_options.get(option_text=option_text)
    except QuestionOption.DoesNotExist:
        return None


def get_or_create_quiz_session(quiz, user):
    """Gets or creates quiz session"""
    session, created = QuizSession.objects.get_or_create(
        quiz=quiz,
        user=user,
        is_completed=False,
        defaults={'current_question_index': 0}
    )
    return session


def get_quiz_session_by_id(session_id, user):
    """Gets quiz session by ID for authenticated user"""
    try:
        return QuizSession.objects.get(id=session_id, user=user)
    except QuizSession.DoesNotExist:
        return None


def get_completed_quiz_session(session_id, user):
    """Gets completed quiz session by ID"""
    try:
        return QuizSession.objects.get(
            id=session_id, 
            user=user,
            is_completed=True
        )
    except QuizSession.DoesNotExist:
        return None


def save_quiz_answer(session, question, selected_option):
    """Saves or updates quiz answer"""
    answer, created = QuizAnswer.objects.get_or_create(
        session=session,
        question=question,
        defaults={'selected_option': selected_option}
    )
    if not created:
        answer.selected_option = selected_option
        answer.save()
    return answer


def move_to_next_question(session):
    """Moves to next question or completes quiz"""
    from django.utils import timezone
    
    total_questions = session.quiz.questions.count()
    if session.current_question_index < total_questions - 1:
        session.current_question_index += 1
        session.save()
    else:
        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()
