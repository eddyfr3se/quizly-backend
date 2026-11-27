"""List owned quizzes and provide owner-restricted detail operations."""

from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from auth_app.api.permissions import HasTrustedOrigin
from quiz_app.models import Quiz

from .permissions import IsQuizOwner
from .serializers import QuizSerializer


class QuizListView(ListAPIView):
    """Return the current user's quizzes as an unpaginated array."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, HasTrustedOrigin]
    pagination_class = None
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        """Filter ownership and preload questions for nested serialization."""
        return Quiz.objects.filter(owner=self.request.user).prefetch_related(
            'questions',
        )


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """Read, partially update or delete a quiz after checking ownership."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, HasTrustedOrigin, IsQuizOwner]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']
    queryset = Quiz.objects.prefetch_related('questions')
