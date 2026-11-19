from rest_framework.pagination import LimitOffsetPagination


class BoundedPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 1000
