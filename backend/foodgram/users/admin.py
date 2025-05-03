from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count

from users.models import User, Subscription

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ-панель для управления пользователями."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar',
        'get_recipe_count',
        'get_subscriber_count',
    )
    list_display_links = ('email',)
    list_filter = ('email', 'username')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            recipe_count=Count('recipes', distinct=True),
            subscriber_count=Count('subscribers', distinct=True),
        )
        return queryset

    def get_recipe_count(self, obj):
        return obj.recipe_count
    get_recipe_count.short_description = 'Рецептов'
    get_recipe_count.admin_order_field = 'recipe_count'

    def get_subscriber_count(self, obj):
        return obj.subscriber_count
    get_subscriber_count.short_description = 'Подписчиков'
    get_subscriber_count.admin_order_field = 'subscriber_count'

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
