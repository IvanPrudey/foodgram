from rest_framework import serializers

from djoser.serializers import UserCreateSerializer, UserSerializer

from users.models import User, Subscription


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        ]


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для отображения информации
    о пользователе с проверкой подписки.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        """Проверка наличия подписки."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            subscribed_to=obj
        ).exists()
