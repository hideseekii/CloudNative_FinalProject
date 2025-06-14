# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # 結帳入口：POST 將 session cart 轉成 Order + OrderItem
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),

    # 結帳成功後的訂單確認頁（使用 DetailView，參數 pk）
    path('confirmation/<int:pk>/', views.OrderConfirmationView.as_view(), name='confirmation'),

    # 單筆訂單詳情（你原本的 function view）
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    # 歷史訂單列表
    path('history/', views.order_history, name='order_history'),

    # 新增/修改評論後
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    path('generate-monthly-report/', views.generate_monthly_report, name='generate_monthly_report'),

    path('staff/order/', views.staff_order_list, name='staff_order_list'),
    path('staff/order/<int:order_id>/complete/', views.mark_order_complete, name='mark_order_complete'),
    
]
