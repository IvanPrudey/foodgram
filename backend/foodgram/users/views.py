from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.pagination import CustomPagination
from users.models import User, Subscription
from users.serializers import CustomUserSerializer

User = get_user_model()


@require_GET
def short_url(request, pk):
    url = reverse('recipes', args=[pk])
    return redirect(url)


class CustomUserViewSet(UserViewSet):
    """
    Кастомный ViewSet для пользователей,
    расширяющий стандартный UserViewSet функционалом подписок.
    """

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @staticmethod
    def process_subscription(request, author):
        """Вспомогательный метод для обработки логики создания подписки."""
        user = request.user
        if not Subscription.objects.filter(user=user, author=author).exists():
            serializer = SubscriptionSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {'detail': 'Подписка уже существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True, methods=['POST'], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        """Подписать текущего пользователя на автора."""
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        return self.process_subscription(request, author)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Отписать текущего пользователя от автора."""
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        subscription = get_object_or_404(
            Subscription, user=request.user, author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Cписок авторов, на которых подписан текущий пользователь."""
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
