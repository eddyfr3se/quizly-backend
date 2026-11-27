"""Store owned quizzes and their ordered questions."""

from django.conf import settings
from django.db import models

from .validators import validate_question_options


class Quiz(models.Model):
    """Store quiz metadata and the account that owns it."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='quizzes',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Show the newest quizzes first, with stable ordering for ties."""

        ordering = ('-created_at', '-id')
        verbose_name_plural = 'quizzes'

    def __str__(self):
        """Use the quiz title in admin selectors and the shell."""
        return self.title


class Question(models.Model):
    """Store a quiz question, its answer options and the correct answer."""

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions',
    )
    question_title = models.TextField()
    question_options = models.JSONField(
        default=list, validators=[validate_question_options],
    )
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Keep questions in their insertion order."""

        ordering = ('id',)

    def __str__(self):
        """Return a short question label for admin selectors."""
        return self.question_title[:80]
