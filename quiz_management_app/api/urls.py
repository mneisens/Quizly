from django.urls import path
from . import views

urlpatterns = [
    path('createQuiz/', views.CreateQuizView.as_view(), name='create_quiz'),
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quizzes/<quiz_id>/start/', views.StartQuizView.as_view(), name='start_quiz'),
    path('sessions/<int:session_id>/submit/', views.SubmitAnswerView.as_view(), name='submit_answer'),
    path('sessions/<int:session_id>/evaluation/', views.QuizEvaluationView.as_view(), name='quiz_evaluation'),
]