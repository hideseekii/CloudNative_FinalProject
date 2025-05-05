# urls.py
from django.urls import path
from .views import HomeView

urlpatterns = [
    # 其他 URL
    path('', HomeView.as_view(), name='home'),
]