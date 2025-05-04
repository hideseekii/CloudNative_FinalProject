# users/views.py
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import views as auth_views
from .forms import CustomerSignUpForm, StaffSignUpForm

# 顧客註冊
class CustomerSignUpView(generic.CreateView):
    form_class    = CustomerSignUpForm
    template_name = 'users/account/signup_customer.html'
    success_url   = reverse_lazy('login')

# 員工註冊
class StaffSignUpView(generic.CreateView):
    form_class    = StaffSignUpForm
    template_name = 'users/account/signup_staff.html'
    success_url   = reverse_lazy('login')


# 登入
class LoginView(auth_views.LoginView):
    template_name = 'users/account/login.html'

# 登出
class LogoutView(auth_views.LogoutView):
    template_name = 'users/account/logged_out.html'

# 密碼變更
class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'users/account/password_change_form.html'
    success_url   = reverse_lazy('password_change_done')

class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'users/account/password_change_done.html'

# 密碼重設：輸入 email
class PasswordResetView(auth_views.PasswordResetView):
    template_name       = 'users/account/password_reset_form.html'
    email_template_name = 'users/account/password_reset_email.html'
    success_url         = reverse_lazy('password_reset_done')

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'users/account/password_reset_done.html'

# 重設連結點開後：設定新密碼
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'users/account/password_reset_confirm.html'
    success_url   = reverse_lazy('password_reset_complete')

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'users/account/password_reset_complete.html'
