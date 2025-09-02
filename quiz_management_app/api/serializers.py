from rest_framework import serializers
from ..models import Quiz, Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    question_options = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer']
    
    def get_question_options(self, obj):
        return [option.option_text for option in obj.question_options.all()]
    
    def get_answer(self, obj):
        correct_option = obj.question_options.filter(is_correct=True).first()
        return correct_option.option_text if correct_option else None


class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at']


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at', 'questions']


class CreateQuizSerializer(serializers.Serializer):
    youtube_url = serializers.URLField()
