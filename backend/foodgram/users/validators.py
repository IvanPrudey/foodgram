import re

from django.core.exceptions import ValidationError

from users.constants import PATTERN_MES


def validate_username_me(value):
    """Валидация: username != me."""
    if value == 'me':
        raise ValidationError(
            ('Имя пользователя не может быть <me>.'),
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
