# menu/urls/public.py
from django.urls import path
from menu.views.public import DishListView, DishDetailView, add_to_cart, remove_from_cart

# REMOVE the app_name line
app_name = 'menu'  

urlpatterns = [
    path('', DishListView.as_view(), name='dish_list'),
    path('dishes/<int:pk>/', DishDetailView.as_view(), name='dish_detail'),
    path('cart/add/<int:pk>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', remove_from_cart, name='remove_from_cart'),
]