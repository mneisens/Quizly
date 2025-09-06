from rest_framework import serializers
from ..models import Quiz, Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Serializer for question options"""
    
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions with options and answers"""
    question_options = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer']
    
    def get_question_options(self, question_obj):
        """Gets all options for a question"""
        return [option.option_text for option in question_obj.question_options.all()]
    
    def get_answer(self, question_obj):
        """Gets the correct answer for a question"""
        correct_option = question_obj.question_options.filter(is_correct=True).first()
        return correct_option.option_text if correct_option else None


class QuizSerializer(serializers.ModelSerializer):
    """Basic serializer for quiz list view"""
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at']


class QuizDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for quiz with questions"""
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'video_url', 'created_at', 'questions']


class CreateQuizSerializer(serializers.Serializer):
    """Serializer for quiz creation input"""
    youtube_url = serializers.URLField()