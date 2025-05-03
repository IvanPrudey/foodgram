import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count, F
from djoser.serializers import UserCreateSerializer, UserSerializer
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
from users.constants import LONG_TEXT
from users.models import Subscription


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Для обработки изображений, преобразует строку base64 в файл."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(
        max_length=LONG_TEXT,
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'id',
        ]


class UserSerializer(UserSerializer):
    """
    Сериализатор для отображения информации
    о пользователе с проверкой подписки.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        ]
        read_only_fields = ['id', 'is_subscribed']

    def get_is_subscribed(self, obj):
        """Проверка наличия подписки."""
        request = self.context.get('request')
        return (
            not request.user.is_anonymous
            and request.user.subscriptions.filter(
                subscribed_to=obj
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для аватара пользователя,
    поддерживающий загрузку в формате base64.
    """

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Для отображения ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Для отображения тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


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
    """Сериализатор для корзины покупок."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')


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
        if user.subscriptions.filter(subscribed_to=subscribed_to).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        return data

    def to_representation(self, instance):

        author_annotated = User.objects.annotate(
            recipes_count=Count('recipes')
        ).filter(id=instance.subscribed_to.id).first()
        return FollowReadSerializer(
            author_annotated,
            context=self.context
        ).data


class FollowReadSerializer(UserSerializer):
    """Для подписок с информацией о пользователе и его рецептах."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'recipes_count',
            'recipes',
        ]
        read_only_fields = UserSerializer.Meta.read_only_fields + [
            'email',
            'first_name',
            'last_name',
            'username'
        ]

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
        allow_null=False,
        label='images',
        required=True
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
        """
        Валидация ингредиентов, тегов и изображения перед
        созданием/обновлением.
        """
        if 'image' not in self.initial_data or not self.initial_data['image']:
            raise serializers.ValidationError(
                'Поле изображения не может быть пустым!',
                code='invalid'
            )

        ingredients = self.initial_data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                'Должен быть минимум один ингредиент!',
                code='invalid'
            )

        ingredients_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!',
                code='invalid'
            )

        existing_ids = set(Ingredient.objects.filter(
            id__in=ingredients_ids
        ).values_list('id', flat=True))
        if missing_ids := set(ingredients_ids) - existing_ids:
            raise serializers.ValidationError(
                f'Ингредиент с id: {missing_ids} не существует!',
                code='invalid'
            )

        tags = self.initial_data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                'Добавьте минимум один тег!',
                code='invalid'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться!',
                code='invalid'
            )

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

    author = UserSerializer(read_only=True)
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
