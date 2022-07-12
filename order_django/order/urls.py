from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'buyer', views.OrderBuyerViewSet, basename='order-buyer')
router.register(r'seller', views.OrderSellerViewSet, basename='order-seller')

urlpatterns = [
    path('', include(router.urls)),
]

