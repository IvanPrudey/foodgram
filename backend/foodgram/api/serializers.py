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
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписки,
    проверяет уникальность и возвращает данные автора.
    """

    class Meta:
        model = Subscription
        fields = ['user', 'subscribed_to']
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'subscribed_to'],
            )
        ]

    def to_representation(self, instance):
        return ShowSubscriptionsSerializer(instance.subscribed_to, context={
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
            user=request.user, subscribed_to=obj).exists()

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
        return ShowFavoriteSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """Отображение добавления ингредиента в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

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
    def validate_unique(values):
        values_set = set()
        for value in values:
            item = get_object_or_404(
                Ingredient,
                id=value.get('id')
            )
            if item in values_set:
                return True
            values_set.add(item)
        return False

    def validate_ingredients(self, data):
        """Проверяет валидность данных об ингредиентах."""
        ingredients = data
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': VALIDATE_MSG_1}
            )

        ingredients = self.initial_data.get('ingredients')
        if self.validate_unique(ingredients):
            raise serializers.ValidationError(
                {'ingredient': VALIDATE_MSG_2}
            )
        for item in ingredients:
            if int(item['amount']) <= 0:
                raise serializers.ValidationError({
                    'amount': VALIDATE_MSG_3
                })
        return data

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужно выбрать хотя бы один тег!'}
            )
        tags_set = set()
        for tag in tags:
            if tag in tags_set:
                raise serializers.ValidationError(
                    {'tags': 'Теги должны быть уникальными!'}
                )
            tags_set.add(tag)
        return value

    @staticmethod
    def create_or_update_obj(recipe, tags, ingredients):

        for tag in tags:
            recipe.tags.add(tag['id'])
        ingredients_in_recipe = []
        for ingredient in ingredients:
            ingredients_in_recipe.append(
                IngredientInRecipe(
                    ingredient_id=ingredient['id'],
                    recipe=recipe,
                    amount=ingredient['amount']
                )
            )
        recipe.recipe_ingredients.bulk_create(ingredients_in_recipe)
        return recipe

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        return self.create_or_update_obj(recipe, tags, ingredients)

    @transaction.atomic
    def update(self, instance, validated_data):

        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        recipe = super().update(instance, validated_data)
        return self.create_or_update_obj(recipe, tags, ingredients)
