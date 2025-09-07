from rest_framework import serializers
from ..models import Quiz, Question, QuestionOption, QuizSession, QuizAnswer


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
    youtube_url = serializers.URLField(required=False)
    url = serializers.URLField(required=False)
    
    def validate(self, attrs):
        """Validates that either youtube_url or url is provided"""
        youtube_url = attrs.get('youtube_url')
        url = attrs.get('url')
        
        if not youtube_url and not url:
            raise serializers.ValidationError("YouTube URL is required.")
        
        # Use whichever field is provided
        if url:
            attrs['youtube_url'] = url
        
        return attrs


class QuizSessionSerializer(serializers.ModelSerializer):
    """Serializer for quiz session"""
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizSession
        fields = ['id', 'quiz', 'started_at', 'is_completed', 'current_question_index', 'progress_percentage']
    
    def get_progress_percentage(self, session_obj):
        """Gets progress percentage"""
        return session_obj.get_progress_percentage()


class QuizAnswerSerializer(serializers.ModelSerializer):
    """Serializer for quiz answers"""
    
    class Meta:
        model = QuizAnswer
        fields = ['id', 'question', 'selected_option', 'answered_at', 'is_correct']
        read_only_fields = ['is_correct']


class QuizPlayQuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz play questions (without correct answers)"""
    question_options = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options']
    
    def get_question_options(self, question_obj):
        """Gets all options for a question (without is_correct flag)"""
        return [option.option_text for option in question_obj.question_options.all()]


class QuizPlaySerializer(serializers.ModelSerializer):
    """Serializer for quiz play session"""
    current_question = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizSession
        fields = ['id', 'quiz', 'current_question', 'current_question_index', 'progress_percentage', 'total_questions', 'is_completed']
    
    def get_current_question(self, session_obj):
        """Gets current question without correct answers"""
        current_question = session_obj.get_current_question()
        if current_question:
            return QuizPlayQuestionSerializer(current_question).data
        return None
    
    def get_progress_percentage(self, session_obj):
        """Gets progress percentage"""
        return session_obj.get_progress_percentage()
    
    def get_total_questions(self, session_obj):
        """Gets total number of questions"""
        return session_obj.quiz.questions.count()


class SubmitAnswerSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""
    question_id = serializers.IntegerField()
    selected_option_text = serializers.CharField(max_length=200)


class QuizEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for quiz evaluation results"""
    correct_answers = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    answers = QuizAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizSession
        fields = ['id', 'quiz', 'started_at', 'completed_at', 'correct_answers', 'total_questions', 'percentage', 'answers']
    
    def get_correct_answers(self, session_obj):
        """Gets number of correct answers"""
        return session_obj.answers.filter(selected_option__is_correct=True).count()
    
    def get_total_questions(self, session_obj):
        """Gets total number of questions"""
        return session_obj.quiz.questions.count()
    
    def get_percentage(self, session_obj):
        """Calculates percentage score"""
        total = self.get_total_questions(session_obj)
        if total == 0:
            return 0
        correct = self.get_correct_answers(session_obj)
        return round((correct / total) * 100, 1)