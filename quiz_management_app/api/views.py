from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Quiz
from .serializers import QuizSerializer, CreateQuizSerializer


class CreateQuizView(generics.CreateAPIView):
    serializer_class = CreateQuizSerializer
    permission_classes = [IsAuthenticated]
