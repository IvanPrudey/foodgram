from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    short_url,
    TagViewSet
)
from users.views import CustomUserViewSet

app_name = 'api'

router_version_1 = DefaultRouter()
router_version_1.register(r'users', CustomUserViewSet, basename='users')
router_version_1.register(
    r'ingredients', IngredientViewSet, basename='ingredients'
)
router_version_1.register(r'tags', TagViewSet, basename='tags')
router_version_1.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path(
        'recipes/<int:pk>/short-url/',
        short_url,
        name='short_url'
    ),
    path('', include(router_version_1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
