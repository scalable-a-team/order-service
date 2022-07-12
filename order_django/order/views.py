from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from order_django.order.models import Order
from order_django.permissions import IsBuyer
from order_django.settings import KONG_USER_ID


class OrderBuyerViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsBuyer]

    def get_queryset(self):
        user_id = self.request.META[KONG_USER_ID]
        return Order.objects.filter(buyer_id=user_id).order_by('-created_at')
