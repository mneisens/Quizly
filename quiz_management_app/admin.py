from django.contrib import admin
from .models import Quiz, Question, QuestionOption


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [QuestionOptionInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'created_by')
    search_fields = ('title', 'description', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_title', 'quiz', 'answer', 'created_at')
    list_filter = ('created_at', 'quiz')
    search_fields = ('question_title', 'answer', 'quiz__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionOptionInline]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'question_quiz')
    list_filter = ('question__quiz',)
    search_fields = ('text', 'question__question_title')
    
    def question_quiz(self, obj):
        return obj.question.quiz.title if obj.question else ''
    question_quiz.short_description = 'Quiz'
