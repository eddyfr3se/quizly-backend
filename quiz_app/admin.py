"""Manage quizzes and individual questions in the Django admin."""

from django.contrib import admin

from .forms import QuestionAdminForm
from .models import Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Search quiz metadata and display the owner and timestamps."""

    list_display = ('title', 'owner', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('owner',)
    list_select_related = ('owner',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Edit individual questions and validate their answer options."""

    form = QuestionAdminForm
    list_display = ('question_title', 'quiz', 'answer')
    search_fields = ('question_title', 'quiz__title')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('quiz',)
    list_select_related = ('quiz',)
