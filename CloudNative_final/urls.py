from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('menu/', include('menu.urls')),
    path('', include('menu.urls'), name='home'),
    
    path('', RedirectView.as_view(pattern_name='menu:dish_list'), name='home'),

    # Add these lines for Django's auth system
    path('accounts/login/', auth_views.LoginView.as_view(template_name='users/account/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Your other URLs
]