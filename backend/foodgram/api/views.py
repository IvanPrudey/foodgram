from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import Ingredient, Recipe, Tag


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
