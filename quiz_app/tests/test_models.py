"""Check quiz relationships, timestamps and question option validation."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from quiz_app.models import Question, Quiz


class QuizModelTests(TestCase):
    """Exercise persistence and cascading deletion of quiz data."""

    def setUp(self):
        """Create one owner and a quiz without external service calls."""
        self.owner = get_user_model().objects.create_user(
            username='quiz_owner',
        )
        self.quiz = Quiz.objects.create(
            owner=self.owner, title='First quiz', description='Practice',
            video_url='https://www.youtube.com/watch?v=jNQXAC9IVRw',
        )

    def create_question(self):
        """Store one complete question attached to the fixture quiz."""
        return Question.objects.create(
            quiz=self.quiz, question_title='Which option is correct?',
            question_options=['A', 'B', 'C', 'D'], answer='A',
        )

    def test_relations_and_timestamps_are_persisted(self):
        """Link owners and questions with usable reverse relations."""
        question = self.create_question()
        self.assertEqual(self.owner.quizzes.get(), self.quiz)
        self.assertEqual(self.quiz.questions.get(), question)
        self.assertIsNotNone(self.quiz.created_at)
        self.assertIsNotNone(question.created_at)
        self.assertGreaterEqual(self.quiz.updated_at, self.quiz.created_at)
        self.assertEqual(question.question_options, ['A', 'B', 'C', 'D'])

    def test_edit_preserves_creation_time_and_updates_timestamp(self):
        """Save changes without replacing the quiz or its creation time."""
        created = self.quiz.created_at
        updated = self.quiz.updated_at
        self.quiz.title = 'Changed title'
        self.quiz.save()
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.created_at, created)
        self.assertGreaterEqual(self.quiz.updated_at, updated)
        self.assertEqual(self.quiz.title, 'Changed title')

    def test_deleting_quiz_cascades_to_its_questions(self):
        """Remove dependent questions while keeping the owner account."""
        self.create_question()
        self.quiz.delete()
        self.assertFalse(Question.objects.exists())
        owners = get_user_model().objects.filter(pk=self.owner.pk)
        self.assertTrue(owners.exists())

    def test_deleting_owner_cascades_to_quizzes_and_questions(self):
        """Do not leave quiz data behind when its owner is removed."""
        self.create_question()
        self.owner.delete()
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(Question.objects.exists())

    def test_quiz_and_question_ordering_is_stable(self):
        """Return newest quizzes first and questions in insertion order."""
        second = Quiz.objects.create(
            owner=self.owner, title='Second', video_url=self.quiz.video_url,
        )
        first_question = self.create_question()
        second_question = self.create_question()
        self.assertEqual(list(Quiz.objects.all()), [second, self.quiz])
        self.assertEqual(
            list(self.quiz.questions.all()), [first_question, second_question],
        )

    def test_option_defaults_are_not_shared(self):
        """Keep each new question's mutable options list independent."""
        first, second = Question(), Question()
        first.question_options.append('A')
        self.assertEqual(second.question_options, [])

    def test_invalid_option_shapes_are_rejected(self):
        """Reject wrong counts, duplicates, blank strings and nested values."""
        question = self.create_question()
        invalid = [None, {}, ['A'], ['A', 'B', 'C', 'D', 'E'],
                   ['A', 'A', 'B', 'C'], ['A', 'B', 'C', ' '],
                   ['A', 'B', 'C', 4], ['A', 'B', 'C', {}]]
        for options in invalid:
            with self.subTest(options=options):
                question.question_options = options
                with self.assertRaises(ValidationError):
                    question.full_clean()
