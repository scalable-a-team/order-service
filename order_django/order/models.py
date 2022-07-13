import uuid as uuid
from django.db import models

from order_django.core import BaseModel


class Order(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    status = models.CharField(max_length=32, blank=True)
    seller_id = models.PositiveIntegerField(null=True)
    buyer_id = models.PositiveIntegerField()
    product_id = models.PositiveIntegerField()
    total_incl_tax = models.DecimalField(decimal_places=2, max_digits=12, null=True)
    date_shipped = models.DateTimeField(db_index=True, null=True)
