# menu/urls.py
from django.urls import path
from menu.views.public import DishListView, DishDetailView

app_name = 'menu'

urlpatterns = [
    # http://…/menu/       → 列表
    path('', DishListView.as_view(), name='dish_list'),
    # http://…/menu/3/     → 該 id 詳情
    path('<int:pk>/', DishDetailView.as_view(), name='dish_detail'),
]
