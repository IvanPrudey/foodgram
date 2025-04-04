from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

from users.constants import LONG_TEXT, MAX_SIZE_EMAIL
from users.validators import validate_username, validate_username_me


class User(AbstractUser):
    """Пользователь с расширенными полями."""

    username = models.CharField(
        verbose_name='Пользователь',
        max_length=LONG_TEXT,
        unique=True,
        validators=(validate_username, validate_username_me,),
        help_text=(
            'Поле обязательно к заполнению.'
            'Необходимо использовать только буквы и цифры.'
        ),
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.'
        },
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_SIZE_EMAIL,
        unique=True,
        db_index=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=LONG_TEXT,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=LONG_TEXT,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        """Возвращает имя пользователя."""
        return f'{self.username} ({self.email})'


class Subscription(models.Model):
    """
    Модель для хранения информации о подписках пользователей друг на друга.
    Запрещает повторные подписки и подписки на самого себя.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
        help_text='Укажите пользователя, который подписывается'
    )
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор подписки',
        help_text='Укажите пользователя, на которого подписываются'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user', 'subscribed_to')
        constraints = [
            UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_user_subscription'
            ),
        ]

    def __str__(self):
        return f'Подписка: {self.user} -> {self.subscribed_to}'
