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
    # Custom password reset views (MUST come before admin URLs and accounts/)
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Custom password change views
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    

    
    # Original URLs
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('menu/', include(('menu.urls', 'menu'), namespace='menu')),
    path('', RedirectView.as_view(pattern_name='menu:dish_list'), name='home'),
    path('orders/', include('orders.urls')),
    
]