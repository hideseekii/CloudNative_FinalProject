# staff/urls.py
from django.urls import path
from .views import (StaffSignUpView, StaffLoginView, StaffLogoutView,PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    ProfileView, ProfileEditView)

app_name = 'staff'

urlpatterns = [
    path('signup/', StaffSignUpView.as_view(), name='signup'),  # 修改路徑，移除 customer 部分

    path('login/',  StaffLoginView.as_view(),  name='login'),
    path('logout/', StaffLogoutView.as_view(), name='logout'),

    # 密碼變更
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # 密碼重設
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # 個人資料相關 URL
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),

]
