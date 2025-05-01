from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from api.constants import (
    AMOUNT_MAX,
    AMOUNT_MIN,
    COOKING_TIME_MIN,
    ING_MEAS_LENGTH,
    ING_NAME_LENGTH,
    RECIPE_NAME_LENGTH,
    TAG_LENGTH,
)


User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(
        max_length=ING_NAME_LENGTH,
        verbose_name='Название ингредиента',
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=ING_MEAS_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Тег."""

    name = models.CharField(
        max_length=TAG_LENGTH,
        verbose_name='Название тега',
        unique=True
    )
    slug = models.SlugField(
        max_length=TAG_LENGTH,
        verbose_name='Slug',
        unique=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=RECIPE_NAME_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты  в рецепте'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN, f'Минимальное значение - {COOKING_TIME_MIN}'
            )
        ],
        verbose_name='Время приготовления (в минутах)'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Ингредиенты в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='in_recipes',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                AMOUNT_MIN, f'Минимальное значение - {AMOUNT_MIN}'
            ),
            MaxValueValidator(
                AMOUNT_MAX, f'Максимально возможное значение - {AMOUNT_MAX}'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ('ingredient__name',)

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'


class UserRecipeBaseModel(models.Model):
    """Абстрактная базовая модель для рецептов, связанных с пользователем."""

    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_%(class)s'
            )
        ]
        ordering = ('-created_at',)


class ShoppingCart(UserRecipeBaseModel):
    """Корзина ."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_shopping_cart',
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'

    def __str__(self):
        return (
            f'{self.recipe.name} в корзине пользователя {self.user.username}'
        )


class Favorite(UserRecipeBaseModel):
    """Избранные рецепты."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorited_by',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return (
            f'{self.user.username} добавил в корзину {self.recipe.name}'
        )
