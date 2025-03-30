from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import SubscriptionSerializer
from users.models import User, Subscription
from users.serializers import AvatarSerializer, CustomUserSerializer


class CustomUserViewSet(UserViewSet):
    """
    Кастомный ViewSet для пользователей,
    расширяющий стандартный UserViewSet функционалом подписок.
    """

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

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


class UserAvatarUpdateView(RetrieveUpdateDestroyAPIView):
    """
    Представление для работы с аватаром пользователя.
    Обеспечивает получение, обновление и удаление аватара.
    Наследует стандартные CRUD-операции от RetrieveUpdateDestroyAPIView.
    """

    serializer_class = AvatarSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'status': 'Аватар обновлен'},
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        try:
            user: User = self.request.user
            user.avatar = None
            user.save()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as error:
            return Response(
                {'error': str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )
