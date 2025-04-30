from rest_framework.pagination import PageNumberPagination

from api.constants import PAGE_SIZE


class SpecificPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
