from django.contrib import admin
from django.db.models import Count
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ панель для модели Ingredient."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админ панель для модели IngredientInRecipe."""

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('ingredient__name',)
    list_filter = ('ingredient',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ панель для модели Tag."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ('name', 'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ панель для модели Recipe."""

    inlines = (RecipeIngredientInline,)
    list_display = (
        'name', 'author', 'cooking_time', 'favorited_by_count'
    )
    list_display_links = ('name', 'author')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('author', 'tags')
    filter_horizontal = ('tags',)
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
            .annotate(favorited_by_count=Count('favorited_by'))
        )

    def favorited_by_count(self, obj):
        return obj.favorited_by_count
    favorited_by_count.short_description = 'В избранном'
    favorited_by_count.admin_order_field = 'favorited_by_count'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ панель для модели Favorite."""

    list_display = ['user', 'recipe', 'created_at']
    list_display_links = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ панель для модели ShoppingCart."""

    list_display = ['user', 'recipe']
    list_display_links = ['user', 'recipe']
    empty_value_display = '-пусто-'
