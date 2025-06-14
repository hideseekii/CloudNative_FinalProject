from django.urls import path
from . import views
from .views import ReviewListView

app_name = "reviews"

urlpatterns = [
    path('order/<int:order_id>/review/', views.add_review, name='add_review'),
    path('order/<int:order_id>', views.add_dish_review, name='add_dish_review'),
    path('reviews/', ReviewListView.as_view(), name='review_list')
]
