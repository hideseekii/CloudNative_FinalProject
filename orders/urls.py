# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # 結帳，將 ShoppingCart 資料寫進 Order/OrderItem
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    # 結帳成功後的確認頁
    path('confirmation/<int:pk>/', views.OrderConfirmationView.as_view(), name='confirmation'),

    # 單筆訂單明細（可留給後續參考）
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),

    # 歷史訂單列表
    path('history/', views.order_history, name='order_history'),
]
