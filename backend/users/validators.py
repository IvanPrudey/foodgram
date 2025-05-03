import re

from django.core.exceptions import ValidationError

from users.constants import PATTERN_MES, USERNAME_ME


def validate_username_me(value):
    """Валидация: username != me."""
    if value == USERNAME_ME:
        raise ValidationError(
            (f'Имя пользователя не может быть {USERNAME_ME}.'),
            params={'value': value},
        )


def validate_username(username):
    """Проверяет username на соответствие паттерну."""
    pattern = r'^[\w.@+-]+\Z'
    if not re.match(pattern, username):
        raise ValidationError(
            f'{PATTERN_MES}'
        )
    return username
