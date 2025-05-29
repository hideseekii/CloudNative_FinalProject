from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

# Import your custom views

from . import views as heath_views  # Import your custom views

from users.views import (
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)

urlpatterns = [

    # Health check endpoint
    path('health/', heath_views.health_check, name='health_check'),

    
    # Staff URLs
    path('staff/', include(('staff.urls', 'staff'), namespace='staff')),
    
    # Original URLs
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('menu/', include(('menu.urls', 'menu'), namespace='menu')),
    path('', RedirectView.as_view(pattern_name='menu:dish_list'), name='home'),
    path('orders/', include('orders.urls')),
    path('reviews/', include(('reviews.urls', 'reviews'), namespace='reviews')),

    
    path('i18n/setlang/', set_language, name='set_language'),

]
