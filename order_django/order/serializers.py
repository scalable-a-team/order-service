from rest_framework import serializers

from order_django.order.views import Order


class OrderResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['uuid', 'status', 'seller_id', 'buyer_id', 'product_id',
                  'total_incl_tax', 'date_shipped', 'created_at']
