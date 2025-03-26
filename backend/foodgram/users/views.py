from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from users.models import User
from users.serializers import AvatarSerializer


class UserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    pass


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
