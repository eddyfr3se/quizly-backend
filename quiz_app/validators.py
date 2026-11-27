"""Validate the answer options shared by quiz question forms."""

from django.core.exceptions import ValidationError


def validate_question_options(options):
    """Require four distinct nonempty strings in a JSON list."""
    if not isinstance(options, list) or len(options) != 4:
        raise ValidationError('Provide exactly four answer options.')
    if any(not isinstance(item, str) or not item.strip() for item in options):
        raise ValidationError('Answer options must be nonempty strings.')
    if len(set(options)) != 4:
        raise ValidationError('Answer options must be distinct.')
