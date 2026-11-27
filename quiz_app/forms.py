"""Validate question edits in the Django admin."""

from django import forms

from .models import Question


class QuestionAdminForm(forms.ModelForm):
    """Keep a question's correct answer among its answer options."""

    class Meta:
        """Expose the editable question fields."""

        model = Question
        fields = ('quiz', 'question_title', 'question_options', 'answer')

    def clean(self):
        """Report an answer that does not match any supplied option."""
        data = super().clean()
        options = data.get('question_options')
        answer = data.get('answer')
        if isinstance(options, list) and answer and answer not in options:
            self.add_error('answer', 'Select one of the answer options.')
        return data
