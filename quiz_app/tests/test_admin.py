"""Check real admin forms and persistence of quiz and question edits."""

import json
import secrets

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from quiz_app.models import Question, Quiz


class QuizAdminTests(TestCase):
    """Use admin POST requests rather than bypassing the edit forms."""

    def setUp(self):
        """Create a staff account and one quiz for admin editing."""
        self.user = get_user_model().objects.create_superuser(
            username='test_admin', password=secrets.token_urlsafe(24),
        )
        self.client.force_login(self.user)
        self.quiz = Quiz.objects.create(
            owner=self.user, title='Admin quiz', description='Original',
            video_url='https://www.youtube.com/watch?v=jNQXAC9IVRw',
        )

    def question_data(self):
        """Prepare a valid payload in the format expected by admin widgets."""
        return {
            'quiz': self.quiz.pk, 'question_title': 'Choose a letter',
            'question_options': json.dumps(['A', 'B', 'C', 'D']),
            'answer': 'A', '_save': 'Save',
        }

    def test_admin_lists_and_forms_are_available(self):
        """Make both quizzes and individual questions manageable."""
        for name in ('quiz_changelist', 'question_changelist',
                     'quiz_add', 'question_add'):
            with self.subTest(name=name):
                response = self.client.get(reverse('admin:quiz_app_' + name))
                self.assertEqual(response.status_code, 200)

    def test_quiz_metadata_can_be_updated(self):
        """Persist title and description changes through the admin form."""
        url = reverse('admin:quiz_app_quiz_change', args=[self.quiz.pk])
        response = self.client.post(url, {
            'owner': self.user.pk, 'title': 'Updated quiz',
            'description': 'Updated description',
            'video_url': self.quiz.video_url, '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Updated quiz')
        self.assertEqual(self.quiz.description, 'Updated description')

    def test_question_can_be_created_and_edited(self):
        """Save a question, then change its answer in the individual editor."""
        data = self.question_data()
        response = self.client.post(
            reverse('admin:quiz_app_question_add'), data,
        )
        self.assertEqual(response.status_code, 302)
        question = Question.objects.get()
        url = reverse('admin:quiz_app_question_change', args=[question.pk])
        response = self.client.post(url, {**data, 'answer': 'B'})
        self.assertEqual(response.status_code, 302)
        question.refresh_from_db()
        self.assertEqual(question.answer, 'B')

    def test_answer_must_belong_to_options(self):
        """Reject an unmatched answer without storing an invalid question."""
        data = {**self.question_data(), 'answer': 'Not an option'}
        response = self.client.post(
            reverse('admin:quiz_app_question_add'), data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('answer', response.context['adminform'].form.errors)
        self.assertFalse(Question.objects.exists())

    def test_invalid_options_are_rejected_by_admin(self):
        """Reject invalid JSON options without saving the question."""
        for options in (['A', 'B'], ['A', 'A', 'B', 'C'], {'A': 1}, None):
            data = {**self.question_data(),
                    'question_options': json.dumps(options)}
            response = self.client.post(
                reverse('admin:quiz_app_question_add'), data,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                'question_options', response.context['adminform'].form.errors,
            )
        self.assertFalse(Question.objects.exists())

    def test_non_staff_cannot_access_admin(self):
        """Keep quiz administration restricted to staff accounts."""
        self.user.is_staff = False
        self.user.save(update_fields=['is_staff'])
        response = self.client.get(reverse('admin:quiz_app_quiz_changelist'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
