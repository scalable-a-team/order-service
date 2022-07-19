import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from order_django.celery import app as celery_app
from order_django.order.enums import EventStatus, QueueName, OrderStatus
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
            try:
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
            except Exception as e:
                print(e)
                return Response({'error': 'Celery connection failed'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'order_id': order_id}, status=status.HTTP_201_CREATED)


class OrderSellerViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsSeller]
    serializer_class = OrderReadSerializer

    def get_queryset(self):
        user_id = self.request.META[KONG_USER_ID]
        return Order.objects.filter(seller_id=user_id).order_by('-created_at')

    def update(self, request, *args, **kwargs):
        order_instance = self.get_object()
        new_order_status = request.data['new_status']

        if not OrderStatus.is_new_status_valid(order_instance.status, new_order_status):
            return Response({'error': 'Invalid status to transition to'}, status.HTTP_400_BAD_REQUEST)

        if new_order_status == OrderStatus.FAILED:
            context_payload = {}
            PROPAGATOR.inject(carrier=context_payload)
            with tracer.start_span(f"send_task {EventStatus.REJECT_ORDER}"):
                celery_app.send_task(
                    EventStatus.REJECT_ORDER,
                    kwargs={
                        'product_id': order_instance.product_id,
                        'buyer_id': order_instance.buyer_id,
                        'order_id': order_instance.uuid,
                        'price': order_instance.total_incl_tax,
                        'context_payload': context_payload
                    },
                    queue=QueueName.ORDER,
                )
        order_instance.status = new_order_status
        order_instance.save()
        serializer = self.get_serializer(order_instance)
        return Response(serializer.data)
