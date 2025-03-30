from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

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


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Отображение модели, связывающей ингредиенты и рецепт."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'amount', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра модели Рецепт."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def _check_user_relation(self, obj, model):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated and model.objects.filter(
                user=request.user, recipe_id=obj
            ).exists()
        )

    def get_is_favorited(self, obj):
        return self._check_user_relation(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self._check_user_relation(obj, ShoppingCart)


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписки,
    проверяет уникальность и возвращает данные автора.
    """

    class Meta:
        model = Subscription
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data


class ShowSubscriptionsSerializer(serializers.ModelSerializer):
    """
    Для отображения подписок пользователя с информацией
    о подписке, рецептах и их количестве.
    """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()

    def get_recipes(self, obj):
        """Возвращает рецепты автора с возможностью ограничения количества."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=obj)
        limit = request.query_params.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        else:
            recipes = recipes.all()
        return ShowFavoriteSerializer(
            recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return Recipe.objects.filter(author=obj).count()


class ShowFavoriteSerializer(serializers.ModelSerializer):
    """Отображение избранного."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Отображение списка корзины."""

    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShowFavoriteSerializer(instance.recipe, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранными рецептами."""

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        request = self.context.get('request')
        return ShowFavoriteSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Отображение добавления ингредиента в рецепт."""

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'amount']
        extra_kwargs = {
            'id': {'required': True},
            'amount': {'required': True}
        }


class CreateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецептов.
    Обрабатывает данные рецепта, включая ингредиенты, теги и изображение.
    """

    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    @staticmethod
    def _check_unique(values, model=None):
        """Проверка уникальности значений."""
        seen = set()
        for value in values:
            item = value['id'] if model is None else get_object_or_404(
                model, id=value['id']
            )
            if item in seen:
                return True
            seen.add(item)
        return False

    def validate_ingredients(self, data):
        """Проверяет валидность данных об ингредиентах."""
        ingredients = data
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': VALIDATE_MSG_1}
            )

        if self._check_unique(
            self.initial_data.get('ingredients'), Ingredient
        ):
            raise serializers.ValidationError(
                {'ingredient': VALIDATE_MSG_2}
            )

        if any(int(item['amount']) <= 0 for item in ingredients):
            raise serializers.ValidationError(
                {'amount': VALIDATE_MSG_3}
            )
        return data

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                {'tags': 'Нужно выбрать хотя бы один тег!'}
            )

        if self._check_unique(value):
            raise serializers.ValidationError(
                {'tags': 'Теги должны быть уникальными!'}
            )
        return value

    @staticmethod
    def _create_recipe_objects(recipe, tags, ingredients):
        """Создание связанных объектов рецепта."""
        recipe.tags.set(tag['id'] for tag in tags)

        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])
        return recipe

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        return self._create_recipe_objects(recipe, tags, ingredients)

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().update(instance, validated_data)
        return self._create_recipe_objects(recipe, tags, ingredients)
