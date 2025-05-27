from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

# Import your custom views
from users.views import (
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)

urlpatterns = [
    
    # Staff URLs
    path('staff/', include(('staff.urls','staff'), namespace='staff')),
    
    # Original URLs
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('menu/', include(('menu.urls', 'menu'), namespace='menu')),
    path('', RedirectView.as_view(pattern_name='menu:dish_list'), name='home'),
    path('orders/', include('orders.urls')),
    path('reviews/', include('reviews.urls')),
    
]