from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Quiz
from .serializers import QuizSerializer, QuizDetailSerializer, CreateQuizSerializer


class CreateQuizView(generics.CreateAPIView):
    serializer_class = CreateQuizSerializer
    permission_classes = [IsAuthenticated]


class QuizListView(generics.ListAPIView):
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = QuizDetailSerializer(instance)
        return Response(serializer.data)
