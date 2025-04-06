from django.contrib import admin
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

    list_display = ('id', 'name', 'color', 'slug')
    list_display_links = ('name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('color',)
    empty_value_display = '-пусто-'
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ панель для модели Recipe."""

    list_display = (
        'name', 'author', 'cooking_time'
    )
    list_display_links = ('name', 'author')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('author', 'tags')
    filter_horizontal = ('ingredients', 'tags')
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
        )


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
