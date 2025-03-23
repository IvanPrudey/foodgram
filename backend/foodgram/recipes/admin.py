from django.contrib import admin
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ панель для модели Ingredient."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админ панель для модели IngredientInRecipe."""
    list_display = ('ingredient', 'amount')
    search_fields = ('ingredient__name',)
    list_filter = ('ingredient',)
    empty_value_display = '-пусто-'

    class Meta:
        verbose_name = 'ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ панель для модели Tag."""
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('color',)
    empty_value_display = '-пусто-'

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ панель для модели Recipe."""
    list_display = (
        'name', 'author', 'cooking_time', 'pub_date'
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('author', 'tags', 'pub_date')
    filter_horizontal = ('ingredients', 'tags')
    empty_value_display = '-пусто-'

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
