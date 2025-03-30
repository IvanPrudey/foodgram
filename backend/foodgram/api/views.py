from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShowSubscriptionsSerializer,
    SubscriptionSerializer,
    TagSerializer
)
from api.filters import IngredientFilter
from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


class IngredientViewSet(ReadOnlyModelViewSet):
    """Представление ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = IsAdminOrReadOnly
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    """Представление рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = IsAdminAuthorOrReadOnly
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        return RecipeSerializer if self.request.method == 'GET' else CreateRecipeSerializer # noqa

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def _process_action(self, request, pk, serializer_class, model=None):
        data = {'user': request.user.id, 'recipe': pk}

        if model:
            recipe = get_object_or_404(Recipe, id=pk)
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def add_to_favorites(self, request, pk=None):
        return self._process_action(request, pk, FavoriteSerializer)

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, pk=None):
        favorite = get_object_or_404(
            Favorite,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], detail=True)
    def add_to_shopping_cart(self, request, pk=None):
        return self._process_action(
            request, pk, ShoppingCartSerializer, ShoppingCart
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        shopping_cart = get_object_or_404(
            ShoppingCart,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk))
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        ingredient_list = '\n'.join(
            f'{ing["ingredient__name"]} - {ing["amount"]} {ing["ingredient__measurement_unit"]}' # noqa
            for ing in ingredients
        )
        response = HttpResponse(ingredient_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shop_list.txt"' # noqa
        return response


class TagViewSet(ReadOnlyModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = IsAdminOrReadOnly


class SubscribeView(APIView):
    """Представление для подписки и отписки на авторов."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        subscription_data = {
            'user': request.user.id,
            'author': id
        }

        serializer = SubscriptionSerializer(
            data=subscription_data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        subscription_exists = Subscription.objects.filter(
            user=request.user,
            author=author
        ).exists()

        if not subscription_exists:
            return Response(
                {'detail': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=author
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShowSubscriptionsView(ListAPIView):
    """
    API для получения списка авторов,
    на которых подписан текущий пользователь.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ShowSubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(author__user=self.request.user)
