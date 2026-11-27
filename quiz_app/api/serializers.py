"""Serialize quizzes and questions using the documented response fields."""

from rest_framework import serializers

from quiz_app.models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    """Return question data without allowing edits through the quiz API."""

    class Meta:
        """Keep nested fields aligned with the read endpoint examples."""

        model = Question
        fields = ('id', 'question_title', 'question_options', 'answer')
        read_only_fields = fields


class QuizSerializer(serializers.ModelSerializer):
    """Return full quiz data and accept only metadata changes."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        """Expose documented fields with title and description editable."""

        model = Quiz
        fields = (
            'id', 'title', 'description', 'created_at', 'updated_at',
            'video_url', 'questions',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'video_url', 'questions',
        )

    def validate(self, attrs):
        """Reject attempts to update anything except title and description."""
        unsupported = set(self.initial_data) - {'title', 'description'}
        if unsupported:
            raise serializers.ValidationError({
                name: 'This field cannot be updated.' for name in unsupported
            })
        return attrs
