# menu/urls.py
from django.urls import include, path

app_name = 'menu'
urlpatterns = [
    path('', include('menu.urls.public', namespace='public')),
    # … customer/ 和 staff/ 路由 …
]
