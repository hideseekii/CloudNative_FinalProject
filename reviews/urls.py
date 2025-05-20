from django.urls import path
from . import views

urlpatterns = [
    path('order/<int:order_id>/review/', views.add_review, name='add_review'),
    #path('order/<int:order_id>/dish_review/', views.add_dish_review, name='add_dish_review'),
]