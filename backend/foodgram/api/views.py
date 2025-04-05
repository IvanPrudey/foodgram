from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.permissions import IsAdminAuthorOrReadOnly
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
from api.filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


# @require_GET
# def short_url(request, pk):
#     url = reverse('recipes', args=[pk])
#     return redirect(url)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Представление ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Представление рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAdminAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @staticmethod
    def process_favorite(request, pk, serializer_class):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def add_to_favorites(self, request, pk=None):
        return self.process_favorite(
            request=request, pk=pk,
            serializer_class=FavoriteSerializer)

    @add_to_favorites.mapping.delete
    def remove_from_favorites(self, request, pk=None):
        return self.process_favorite(
            request=request, pk=pk,
            serializer_class=FavoriteSerializer
        )

    @staticmethod
    def process_shopping_cart(request, pk, serializer_class):
        data = {'user': request.user.id, 'recipe': pk}
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            serializer = serializer_class(
                data=data, context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def add_to_shopping_cart(self, request, pk=None):
        return self.process_shopping_cart(
            request=request, pk=pk, serializer_class=ShoppingCartSerializer
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        instance = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).first()
        if instance:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в корзине.'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(methods=['GET'], detail=False)
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        ingredient_lines = []
        for ingredient_data in ingredients:
            line = (
                f'{ingredient_data["ingredient__name"]} - '
                f'{ingredient_data["amount"]} '
                f'{ingredient_data["ingredient__measurement_unit"]}'
            )
            ingredient_lines.append(line)

        ingredient_list = ','.join(ingredient_lines)

        file_name = 'shopping_list'
        response = HttpResponse(
            ingredient_list, content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{file_name}.pdf"'
        )
        return response


class TagViewSet(ReadOnlyModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrAuthorOrReadOnly]
    pagination_class = None


# class SubscribeView(APIView):
#     """Представление для подписки и отписки на авторов."""

#     permission_classes = [IsAuthenticated]

#     def post(self, request, id):
#         subscription_data = {
#             'user': request.user.id,
#             'subscribed_to': id
#         }

#         serializer = SubscriptionSerializer(
#             data=subscription_data,
#             context={'request': request}
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, id):
#         subscribe_to = get_object_or_404(User, id=id)
#         if Subscription.objects.filter(
#            user=request.user, subscribe_to=subscribe_to).exists():
#             subscription = get_object_or_404(
#                 Subscription, user=request.user, subscribe_to=subscribe_to
#             )
#             subscription.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         return Response(status=status.HTTP_400_BAD_REQUEST)


# class ShowSubscriptionsView(ListAPIView):
#     """
#     API для получения списка авторов,
#     на которых подписан текущий пользователь.
#     """

#     permission_classes = [IsAuthenticated]
#     serializer_class = ShowSubscriptionsSerializer
#     pagination_class = CustomPagination

#     def get_queryset(self):
#         user = self.request.user
#         return User.objects.filter(subscribed_to__user=user)
