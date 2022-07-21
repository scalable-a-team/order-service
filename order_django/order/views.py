import uuid

from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from order_django import settings
from order_django.celery import app as celery_app
from order_django.order.enums import EventStatus, QueueName, OrderStatus
from order_django.order.models import Order
from order_django.order.serializers import OrderReadSerializer
from order_django.permissions import IsBuyer, IsSeller
from order_django.settings import KONG_USER_ID
from opentelemetry import propagate, trace
import requests

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
        job_description = request.data['job_description']
        dimension = request.data['dimension']

        response = requests.get(f'{settings.PRODUCT_SERVICE_URL}/{product_id}')
        if not response.ok:
            return Response({'error': 'Failed to connect to product retrieve endpoint'})

        product_data = response.json()
        seller_id = product_data['seller_id']
        price = product_data['price']

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
                        'seller_id': seller_id,
                        'product_amount': price,
                        'job_description': job_description,
                        'dimension': dimension,
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

        context_payload = {}
        PROPAGATOR.inject(carrier=context_payload)

        event = OrderStatus.get_event_from_new_status(new_order_status)

        with tracer.start_span(f"send_task {event}"):
            try:
                celery_app.send_task(
                    event,
                    kwargs={
                        'buyer_id': order_instance.buyer_id,
                        'seller_id': order_instance.seller_id,
                        'product_amount': order_instance.total_incl_tax,
                        'order_id': order_instance.uuid,
                        'context_payload': context_payload
                    },
                    queue=QueueName.ORDER,
                )
            except Exception as e:
                print(e)
                return Response({'error': 'Celery connection failed'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=200)
