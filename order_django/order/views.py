import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from order_django.celery import app as celery_app
from order_django.order.enums import EventStatus, QueueName
from order_django.order.models import Order
from order_django.order.serializers import OrderReadSerializer
from order_django.permissions import IsBuyer, IsSeller
from order_django.settings import KONG_USER_ID
from opentelemetry import propagate, trace

PROPAGATOR = propagate.get_global_textmap()
tracer = trace.get_tracer(__name__)

class OrderBuyerViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsBuyer]
    serializer_class = OrderReadSerializer

    def get_queryset(self):
        user_id = self.request.META[KONG_USER_ID]
        return Order.objects.filter(buyer_id=user_id).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        user_id = self.request.META[KONG_USER_ID]
        product_id = request.data['product_id']
        order_id = uuid.uuid4()
        context_payload = {}
        PROPAGATOR.inject(carrier=context_payload)

        with tracer.start_span(f"send_task {EventStatus.CREATE_ORDER}"):
            celery_app.send_task(
                EventStatus.CREATE_ORDER,
                kwargs={
                    'product_id': product_id,
                    'buyer_id': user_id,
                    'order_id': order_id,
                    'context_payload': context_payload
                },
                queue=QueueName.ORDER,
            )
        return Response({'order_id': order_id}, status=status.HTTP_201_CREATED)


class OrderSellerViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsSeller]
    serializer_class = OrderReadSerializer

    def get_queryset(self):
        user_id = self.request.META[KONG_USER_ID]
        return Order.objects.filter(seller_id=user_id).order_by('-created_at')
