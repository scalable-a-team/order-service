from rest_framework.permissions import BasePermission

from order_django.settings import KONG_USER_GROUP, KONG_ANON_HEADER


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        user_group = request.META.get(KONG_USER_GROUP)
        is_anon = request.META.get(KONG_ANON_HEADER)
        return is_anon != "true" and user_group == "customer"


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        user_group = request.META.get(KONG_USER_GROUP)
        is_anon = request.META.get(KONG_ANON_HEADER)
        return is_anon != "true" and user_group == "seller"
