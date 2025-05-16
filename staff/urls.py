# staff/urls.py
from django.urls import path
from .views import StaffSignUpView, StaffLoginView, StaffLogoutView

app_name = 'staff'

urlpatterns = [
    path('signup/', StaffSignUpView.as_view(), name='signup'),
    path('login/',  StaffLoginView.as_view(),  name='login'),
    path('logout/', StaffLogoutView.as_view(), name='logout'),
    # 之後可以再加 staff-dashboard, 菜單管理等等
]
