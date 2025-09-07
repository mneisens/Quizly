from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    """Model representing a quiz"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of quiz"""
        return self.title


class Question(models.Model):
    """Model representing a question in a quiz"""
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_title = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """String representation of question"""
        return self.question_title


class QuestionOption(models.Model):
    """Model representing an option for a question"""
    question = models.ForeignKey(Question, related_name='question_options', on_delete=models.CASCADE)
    option_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        """String representation of question option"""
        return self.option_text


class QuizSession(models.Model):
    """Model representing a quiz playing session"""
    quiz = models.ForeignKey(Quiz, related_name='sessions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    current_question_index = models.IntegerField(default=0)
    
    def __str__(self):
        """String representation of quiz session"""
        return f"{self.user.username} - {self.quiz.title}"

    def get_current_question(self):
        """Gets the current question based on index"""
        questions = self.quiz.questions.all().order_by('id')
        if 0 <= self.current_question_index < questions.count():
            return questions[self.current_question_index]
        return None

    def get_progress_percentage(self):
        """Calculates progress percentage"""
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            return 0
        return (self.current_question_index / total_questions) * 100


class QuizAnswer(models.Model):
    """Model representing a user's answer to a question"""
    session = models.ForeignKey(QuizSession, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        """String representation of quiz answer"""
        return f"{self.session.user.username} - {self.question.question_title}"

    def is_correct(self):
        """Checks if the selected option is correct"""
        return self.selected_option.is_correct