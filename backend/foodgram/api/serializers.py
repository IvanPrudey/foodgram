from rest_framework.serializers import ModelSerializer

from recipes.models import Ingredient, Recipe, Tag


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeSerializer(ModelSerializer):

    class Meta:
        model = Recipe
