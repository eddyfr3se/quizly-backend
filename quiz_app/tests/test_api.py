"""Check quiz responses, ownership and read/update/delete behavior."""

import secrets

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APITestCase

from quiz_app.models import Question, Quiz


class QuizAPITests(APITestCase):
    """Use real cookie login for owned and foreign quiz requests."""

    def setUp(self):
        """Create two owners and log in with the first account."""
        self.password = secrets.token_urlsafe(24)
        self.user = get_user_model().objects.create_user(
            username='quiz_owner', password=self.password,
        )
        self.other = get_user_model().objects.create_user(username='other')
        self.quiz = self.make_quiz(self.user, 'Owned quiz')
        self.foreign = self.make_quiz(self.other, 'Foreign quiz')
        self.question = self.make_question(self.quiz)
        self.url = reverse('quiz-detail', args=[self.quiz.pk])
        self.client.post(reverse('login'), {
            'username': self.user.username, 'password': self.password,
        })

    def make_quiz(self, owner, title):
        """Create quiz metadata without invoking external services."""
        return Quiz.objects.create(
            owner=owner, title=title, description='Description',
            video_url='https://www.youtube.com/watch?v=jNQXAC9IVRw',
        )

    def make_question(self, quiz):
        """Attach a valid question for nested response checks."""
        return Question.objects.create(
            quiz=quiz, question_title='Pick a letter',
            question_options=['A', 'B', 'C', 'D'], answer='A',
        )

    def assert_quiz_shape(self, data):
        """Require the documented response fields without owner information."""
        self.assertEqual(set(data), {
            'id', 'title', 'description', 'created_at', 'updated_at',
            'video_url', 'questions',
        })
        self.assertEqual(set(data['questions'][0]), {
            'id', 'question_title', 'question_options', 'answer',
        })
        self.assertEqual(data['questions'][0]['question_options'],
                         ['A', 'B', 'C', 'D'])

    def test_list_returns_only_owned_quizzes_as_an_array(self):
        """Do not leak foreign quizzes or wrap the result in pagination."""
        response = self.client.get(reverse('quiz-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        owned_ids = [item['id'] for item in response.data]
        self.assertEqual(owned_ids, [self.quiz.pk])
        self.assert_quiz_shape(response.data[0])

    def test_empty_list_is_an_empty_array(self):
        """Return an empty successful list for a user with no quizzes."""
        self.quiz.delete()
        response = self.client.get(reverse('quiz-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_detail_includes_question_fields_and_timestamps(self):
        """Return the complete owned quiz and its nested questions."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assert_quiz_shape(response.data)
        self.assertEqual(response.data['id'], self.quiz.pk)
        self.assertTrue(response.data['created_at'].endswith('Z'))
        self.assertEqual(response.data['questions'][0]['id'], self.question.pk)

    def test_unauthenticated_operations_return_401(self):
        """Require valid access cookies for all quiz operations."""
        self.client.cookies.clear()
        requests = [('get', reverse('quiz-list')), ('get', self.url),
                    ('patch', self.url), ('delete', self.url)]
        for method, url in requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 401)

    def test_foreign_quiz_returns_403_without_changes(self):
        """Distinguish a denied existing object from a missing object."""
        url = reverse('quiz-detail', args=[self.foreign.pk])
        for method in ('get', 'patch', 'delete'):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 403)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, 'Foreign quiz')

    def test_missing_quiz_returns_404(self):
        """Keep missing identifiers distinct for each detail operation."""
        url = reverse('quiz-detail', args=[999999])
        for method in ('get', 'patch', 'delete'):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 404)

    def test_title_patch_returns_the_full_quiz(self):
        """Persist a title-only update while retaining all other data."""
        created = self.quiz.created_at
        data = {'title': 'Updated'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assert_quiz_shape(response.data)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Updated')
        self.assertEqual(self.quiz.description, 'Description')
        self.assertEqual(self.quiz.created_at, created)
        self.assertGreaterEqual(self.quiz.updated_at, created)
        self.assertEqual(self.quiz.questions.get().pk, self.question.pk)

    def test_description_patch_does_not_require_title(self):
        """Allow partial description changes, including clearing its text."""
        for description in ('New description', ''):
            response = self.client.patch(
                self.url, {'description': description}, format='json',
            )
            self.assertEqual(response.status_code, 200)
            self.quiz.refresh_from_db()
            self.assertEqual(self.quiz.description, description)
            self.assertEqual(self.quiz.title, 'Owned quiz')

    def test_invalid_metadata_does_not_save(self):
        """Reject blank/long/null titles and null or malformed descriptions."""
        invalid = [{'title': ''}, {'title': 'x' * 256}, {'title': None},
                   {'description': None}, {'description': {}}]
        for data in invalid:
            with self.subTest(data=data):
                response = self.client.patch(self.url, data, format='json')
                self.assertEqual(response.status_code, 400)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Owned quiz')
        self.assertEqual(self.quiz.description, 'Description')

    def test_readonly_and_unknown_fields_are_rejected(self):
        """Prevent reassignment and nested or server-managed field writes."""
        for field in ('owner', 'id', 'video_url', 'questions',
                      'created_at', 'updated_at', 'unknown'):
            response = self.client.patch(
                self.url, {'title': 'Should not save', field: None},
                format='json',
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Owned quiz')
        self.assertEqual(self.quiz.owner_id, self.user.pk)

    def test_malformed_json_is_rejected(self):
        """Return a controlled error without changing the quiz."""
        response = self.client.patch(
            self.url, '{', content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_returns_204_and_cascades(self):
        """Delete only the owned quiz and its dependent questions."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')
        self.assertFalse(Quiz.objects.filter(pk=self.quiz.pk).exists())
        self.assertFalse(Question.objects.filter(pk=self.question.pk).exists())
        self.assertTrue(Quiz.objects.filter(pk=self.foreign.pk).exists())
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_unsupported_methods_do_not_add_extra_operations(self):
        """Do not expose PUT or quiz generation before its planned stage."""
        self.assertEqual(self.client.put(self.url, {}).status_code, 405)
        for method in ('post', 'put', 'patch', 'delete'):
            response = getattr(self.client, method)(reverse('quiz-list'))
            self.assertEqual(response.status_code, 405)

    def test_foreign_origin_cannot_change_or_delete(self):
        """Apply the shared origin policy to quiz write operations."""
        for method in ('patch', 'delete'):
            response = getattr(self.client, method)(
                self.url, HTTP_ORIGIN='https://example.org',
            )
            self.assertEqual(response.status_code, 403)
        self.assertTrue(Quiz.objects.filter(pk=self.quiz.pk).exists())

    def test_nested_list_does_not_add_queries_per_quiz(self):
        """Keep related-question loading constant as the owned list grows."""
        with CaptureQueriesContext(connection) as small:
            self.client.get(reverse('quiz-list'))
        for index in range(5):
            self.make_question(self.make_quiz(self.user, f'Quiz {index}'))
        with CaptureQueriesContext(connection) as larger:
            response = self.client.get(reverse('quiz-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(len(small), len(larger))
