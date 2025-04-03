from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.serializers import SubscriptionSerializer
from users.models import User, Subscription
from users.serializers import CustomUserSerializer


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
