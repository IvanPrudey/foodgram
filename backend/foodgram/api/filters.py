from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Tags'
    )
    is_favorited = filters.BooleanFilter(method='filter_boolean_field')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_boolean_field')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_boolean_field(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return queryset
        lookup = f"{name.split('_', 1)[1]}__user"
        return queryset.filter(
            **{lookup: self.request.user}
        ) if value else queryset.exclude(**{lookup: self.request.user})
