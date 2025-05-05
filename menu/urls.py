# menu/urls.py
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # 公開區域
    path('', views.DishListView.as_view(), name='dish_list'),
    path('<int:pk>/', views.DishDetailView.as_view(), name='dish_detail'),
    
    # 購物車功能
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_view, name='cart'),
]