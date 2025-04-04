from django.contrib import admin

from users.models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель для управления пользователями."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar'
    )
    list_display_links = ('email',)
    list_filter = ('email', 'username')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель подписки."""

    list_display = ('user', 'subscribed_to')
    list_display_links = ('user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')
    list_filter = ('user', 'subscribed_to')
    fields = ('user', 'subscribed_to')

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'subscribed_to')
        )
