from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('menu/', include('menu.urls')),
    path('', RedirectView.as_view(pattern_name='menu:dish_list'), name='home'),
    path('orders/', include('orders.urls')),
    
    # Specify custom login template
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='users/account/login.html'
    ), name='login'),
    
    # Other auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
]