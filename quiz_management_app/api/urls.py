from django.urls import path
from . import views

urlpatterns = [
    path('test-youtube/', views.TestYouTubeURLView.as_view(), name='test_youtube_url'),
    path('test-system/', views.TestSystemView.as_view(), name='test_system'),
    path('createQuiz/', views.CreateQuizView.as_view(), name='create_quiz'),
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
]
