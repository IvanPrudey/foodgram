from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.pagination import SpecificPagination
from api.permissions import IsAdminOrAuthorOrReadOnly
from api.serializers import FollowCreateSerializer, FollowReadSerializer
from users.models import Subscription
from users.serializers import AvatarSerializer, UserSerializer


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
        methods=['PUT', 'DELETE'],
        detail=False,
        permission_classes=[IsAuthenticated, IsAdminOrAuthorOrReadOnly],
        url_path='me/avatar',
    )
    def avatar_put_delete(self, request, *args, **kwargs):
        if self.request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif self.request.method == 'DELETE':
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
        else:
            deleted_count, _ = Subscription.objects.filter(
                user=user, subscribed_to__id=id
            ).delete()

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
