from django.contrib import admin

from users.models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель для управления пользователями."""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar'
    )
    list_filter = ('email', 'username')
    search_fields = ('username',)
    ordering = ('username',)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель подписки."""

    list_display = ('id', 'user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')
    list_filter = ('user', 'subscribed_to')
    fields = ('user', 'subscribed_to')
