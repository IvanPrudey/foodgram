from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from colorfield.fields import ColorField


User = get_user_model()

AMOUNT_MIN = 1
AMOUNT_MAX = 5000


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(
        max_length=128,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingredient_name_unit_unique'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Тег."""

    name = models.CharField(
        max_length=200,
        verbose_name='Название тега',
        unique=True
    )
    color = ColorField(
        format='hex',
        default='#889977',
        unique=True,
        verbose_name='Цвет в формате HEX'
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        unique=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256,
    )
    image = models.ImageField(
        blank=True,
        verbose_name='Изображение',
        upload_to='recipes/images'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты  в рецепте',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное значение - 1')
        ],
        verbose_name='Время приготовления (в минутах)'
    )
    favorite = models.ManyToManyField(
        User,
        through='Favorite',
        related_name='favorite_recipes',
        blank=True,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

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
        default_related_name = 'ingridients_recipe'
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ['ingredient__name']

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'


# class RecipeTag(models.Model):
#     """Связь тега и рецепта."""

#     recipe = models.ForeignKey(
#         Recipe,
#         on_delete=models.CASCADE,
#         verbose_name='Рецепт'
#     )
#     tag = models.ForeignKey(
#         Tag,
#         on_delete=models.CASCADE,
#         verbose_name='Тег'
#     )

#     class Meta:
#         constraints = [
#             UniqueConstraint(
#                 fields=['recipe', 'tag'],
#                 name='recipe_tag_unique'
#             )
#         ]


class ShoppingCart(models.Model):
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
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_shoppingcart_unique'
            )
        ]
        ordering = ['user', 'recipe']
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'

    def __str__(self):
        return (
            f'{self.recipe.name} в корзине пользователя {self.user.username}'
        )


class Favorite(models.Model):
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
        related_name='favorites',
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='user_favorite_unique'
            )
        ]
        ordering = ['-created_at']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return (
            f'{self.user.username} добавил в корзину {self.recipe.name}'
        )
