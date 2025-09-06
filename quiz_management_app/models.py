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