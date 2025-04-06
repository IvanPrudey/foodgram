from django.contrib.auth import get_user_model
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import User, Subscription
from users.serializers import CustomUserSerializer


VALIDATE_MSG_1 = 'Должно быть наличие хотя бы одного ингредиента!'
VALIDATE_MSG_2 = 'Ингредиенты должны быть уникальными!'
VALIDATE_MSG_3 = 'Укажите положительное количество каждого ингредиента!'

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Для отображения ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Для отображения тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранными рецептами."""

    user = serializers.ReadOnlyField(source='user.id')
    recipe = serializers.ReadOnlyField(source='recipe.id')

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Отображение списка корзины."""

    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart


class FollowCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки на пользователя с валидацией."""

    class Meta:
        model = Subscription
        fields = ('subscribed_to', 'user')

    def validate(self, data):
        request = self.context['request']
        user = request.user
        subscribed_to = data['subscribed_to']
        if user == subscribed_to:
            raise ValidationError('Невозможно подписаться на себя!')
        if Subscription.objects.filter(
            user=user, subscribed_to=subscribed_to
        ).exists():
            raise ValidationError('Вы уже подписаны на этого пользователя!')
        return data


class FollowReadSerializer(serializers.ModelSerializer):
    """Для подписок с информацией о пользователе и его рецептах."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta:
        model = User
        fields = (
            'avatar',
            'email',
            'first_name',
            'id',
            'is_subscribed',
            'last_name',
            'recipes_count',
            'recipes',
            'username'
        )
        read_only_fields = (
            'email',
            'first_name',
            'id',
            'last_name',
            'username'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscribed_to=obj, 
            user=request.user
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        try:
            limit = int(request.GET.get('recipes_limit', 6))
        except (AttributeError, TypeError, ValueError):
            limit = 6

        queryset = Recipe.objects.filter(author=obj)[:limit]
        return ShortRecipeSerializer(
            queryset,
            many=True,
            context={'request': request},
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Для краткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания связи ингредиента с рецептом."""

    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения связи ингредиента с рецептом."""

    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = IngredientInRecipe
        fields = (
            'amount',
            'ingredients'
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        label='Tags',
    )
    ingredients = IngredientInRecipeCreateSerializer(
        many=True,
        label='Ingredients',
    )
    image = Base64ImageField(
        allow_null=True,
        label='images'
    )

    class Meta:
        model = Recipe
        fields = (
            'cooking_time',
            'image',
            'ingredients',
            'name',
            'tags',
            'text',
        )

    def validate(self, data):
        """Валидация ингредиентов и тегов перед созданием/обновлением."""
        ingredients = self.initial_data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Должен быть минимум один ингредиент!'
            })
        ingredients_ids = {ingredient['id'] for ingredient in ingredients}
        existing_ids = set(Ingredient.objects.filter(
            id__in=ingredients_ids
        ).values_list('id', flat=True))

        if missing_ids := ingredients_ids - existing_ids:
            raise serializers.ValidationError(
                f'Ингредиент с id: {missing_ids} не существует!'
            )
        tags = self.initial_data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Добавьте минимум один тег!'
            })
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться!')
        return {
            **data,
            'ingredients': ingredients,
            'tags': tags
        }

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context['request'].user
        )
        self._create_recipe_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с очисткой старых ингредиентов и тегов."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.clear()
        IngredientInRecipe.objects.filter(recipe=instance).delete()

        self._create_recipe_ingredients(ingredients, instance)
        instance.tags.set(tags)

        return super().update(instance, validated_data)

    def _create_recipe_ingredients(self, ingredients, recipe):
        """Создание связей рецепта с ингредиентами."""
        recipe_ingredients = [
            IngredientInRecipe(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        """Возвращает данные через сериализатор для чтения."""
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта с дополнительными полями."""

    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'author',
            'cooking_time',
            'id',
            'image',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'tags',
            'text',
        )
        read_only_fields = fields

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов с их количеством."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('in_recipes__amount'),
        )

    def _check_user_status(self, obj, model_class):
        """Проверяет, связан ли рецепт с пользователем"""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and model_class.objects.filter(
                recipe=obj, user=request.user
            ).exists()
        )

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у пользователя."""
        return self._check_user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в корзине у пользователя."""
        return self._check_user_status(obj, ShoppingCart)
