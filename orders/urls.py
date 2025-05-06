# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('history/', views.order_history, name='order_history'),
]