# menu/urls/customer.py
from django.urls import path
from menu.views.customer import (
    CustomerDishListView, CustomerDishDetailView,
    FavoriteListView, OrderHistoryView
)
from django.contrib.auth.decorators import login_required

# 注意：這裡不要再定義 app_name，因為已經在主 urls.py 中定義了

urlpatterns = [
    # 菜單瀏覽 (客戶專屬)
    path('dishes/', login_required(CustomerDishListView.as_view()), name='customer_dish_list'),
    path('dishes/<int:dish_id>/', login_required(CustomerDishDetailView.as_view()), name='customer_dish_detail'),
    
    # 收藏功能
    path('favorites/', login_required(FavoriteListView.as_view()), name='favorites'),
    
    # 訂單歷史
    path('orders/', login_required(OrderHistoryView.as_view()), name='order_history'),
]