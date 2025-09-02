from django.contrib import admin
from .models import Quiz, Question, QuestionOption


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    fields = ['option_text', 'is_correct']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['question_title']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'video_url', 'question_count']
    list_filter = ['created_at', 'created_by']
    search_fields = ['title', 'description', 'video_url']
    readonly_fields = ['created_at']
    inlines = [QuestionInline]
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Anzahl Fragen'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_title', 'quiz', 'option_count', 'correct_answer']
    list_filter = ['quiz', 'quiz__created_at']
    search_fields = ['question_title', 'quiz__title']
    inlines = [QuestionOptionInline]
    
    def option_count(self, obj):
        return obj.question_options.count()
    option_count.short_description = 'Anzahl Antworten'
    
    def correct_answer(self, obj):
        correct_option = obj.question_options.filter(is_correct=True).first()
        return correct_option.option_text if correct_option else 'Keine'
    correct_answer.short_description = 'Korrekte Antwort'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text', 'question', 'is_correct', 'quiz_title']
    list_filter = ['is_correct', 'question__quiz']
    search_fields = ['option_text', 'question__question_title']
    
    def quiz_title(self, obj):
        return obj.question.quiz.title if obj.question else ''
    quiz_title.short_description = 'Quiz'
