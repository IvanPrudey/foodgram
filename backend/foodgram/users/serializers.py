import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.constants import LONG_TEXT

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Для обработки изображений, преобразует строку base64 в файл."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(
        max_length=LONG_TEXT,
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'id',
        ]


class UserSerializer(UserSerializer):
    """
    Сериализатор для отображения информации
    о пользователе с проверкой подписки.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        ]
        read_only_fields = ['id', 'is_subscribed']

    def get_is_subscribed(self, obj):
        """Проверка наличия подписки."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.subscriptions.filter(subscribed_to=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для аватара пользователя,
    поддерживающий загрузку в формате base64.
    """

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)
