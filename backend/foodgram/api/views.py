from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import SpecificPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    FollowCreateSerializer,
    FollowReadSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription


User = get_user_model()


@require_GET
def short_url(request, pk):
    url = reverse('recipes', args=[pk])
    return redirect(url)


class UserViewSet(UserViewSet):
    """
    Кастомный ViewSet для пользователей,
    расширяющий стандартный UserViewSet функционалом подписок.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = SpecificPagination

    def get_permissions(self):
        if self.action == 'me':
            return [
                IsAuthenticated(),
            ]
        return super().get_permissions()

    @action(
        methods=['PUT'],
        detail=False,
        permission_classes=[IsAuthenticated, IsAdminOrAuthorOrReadOnly],
        url_path='me/avatar',
    )
    def avatar_put(self, request, *args, **kwargs):
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar_put.mapping.delete
    def avatar_delete(self, request, *args, **kwargs):
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        user = request.user
        if request.method == 'POST':
            subscribed_to = get_object_or_404(User, id=id)
            serializer = FollowCreateSerializer(
                context={'request': request},
                data={
                    'subscribed_to': subscribed_to.id,
                    'user': user.id
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            author_annotated = User.objects.annotate(
                recipes_count=Count('recipes')
            ).filter(id=id).first()
            serializer = FollowReadSerializer(
                author_annotated,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = Subscription.objects.filter(
            user=user, subscribed_to__id=id).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Вы не подписаны на данного пользователя!'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_name='subscriptions',
        url_path='subscriptions',
    )
    def get_subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribers__user=user).annotate(
            recipes_count=Count('recipes')
        )
        pages = self.paginate_queryset(queryset)
        serializer = FollowReadSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


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

    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = SpecificPagination
    permission_classes = [IsAdminOrAuthorOrReadOnly]
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients', 'tags'
    )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve', 'get-link'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe__in=Recipe.objects.filter(
                    in_shopping_cart__user=request.user
                )
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(sum=Sum('amount'))
        )
        shopping_list = self.add_shopping_list_to_txt(ingredients)
        return HttpResponse(
            shopping_list, content_type='text/plain', status=200
        )

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=[AllowAny],
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        view_name = self.request.resolver_match.view_name
        base_url = reverse(view_name, kwargs={'pk': pk})
        short_link = self.request.build_absolute_uri(base_url)
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def add_to_favorite(self, request, pk):
        user = request.user

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)

            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        'detail': (
                            f'Рецепт "{recipe.name}" уже добавлен'
                            f'в избранное'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = FavoriteSerializer(
                data={'recipe': recipe.id, 'user': user.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(recipe=recipe, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_objects_number, _ = Favorite.objects.filter(
            recipe_id=pk, user=user
        ).delete()

        if deleted_objects_number:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Такого рецепта нет в избранных!'},
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def add_to_shopping_cart(self, request, pk):
        user = request.user

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)

            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {
                        'detail': f'Рецепт "{recipe.name}" уже добавлен '
                        'в список покупок'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id, 'user': user.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(recipe=recipe, user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = ShoppingCart.objects.filter(
            recipe_id=pk, user=user
        ).delete()

        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Данного рецепта нет в списке покупок!'},
            status=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def add_shopping_list_to_txt(ingredients):
        return '\n'.join(
            f'{ingredient["ingredient__name"]} - {ingredient["sum"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            for ingredient in ingredients
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrAuthorOrReadOnly]
    pagination_class = None
