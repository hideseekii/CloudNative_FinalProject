from django.urls import path
from .views import (
    CustomerSignUpView,  # 移除了 StaffSignUpView
    LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
    ProfileView, ProfileEditView,  # 添加個人資料相關視圖
)

urlpatterns = [
    path('signup/', CustomerSignUpView.as_view(), name='signup'),  # 修改路徑，移除 customer 部分

    path('login/',  LoginView.as_view(),  name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

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


