# users/views.py
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import views as auth_views
from .forms import CustomerSignUpForm
from django.contrib import messages
from django.contrib.auth import logout

# 顧客註冊
class CustomerSignUpView(generic.CreateView):
    form_class    = CustomerSignUpForm
    template_name = 'users/account/signup.html'
    success_url   = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "帳號註冊成功！現在您可以登入。")
        return response

# 登入
class LoginView(auth_views.LoginView):
    template_name = 'users/account/login.html'
    
    def form_valid(self, form):
        messages.success(self.request, f"歡迎回來，{form.get_user().username}！")
        return super().form_valid(form)

class LogoutView(auth_views.LogoutView):
    # 允許 GET/POST
    http_method_names = ['get', 'post', 'head', 'options']
    # 登出後重定向到首頁
    next_page = '/'  # 改為根路徑，即首頁
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, "您已成功登出。")
            logout(request)  # 顯式調用登出功能
        return super().dispatch(request, *args, **kwargs)


# 密碼變更
class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'users/account/password_change_form.html'
    success_url = reverse_lazy('password_change_done')
    
    def form_valid(self, form):
        messages.success(self.request, "您的密碼已成功變更！")
        return super().form_valid(form)

class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'users/account/password_change_done.html'

# 密碼重設：輸入 email
class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'users/account/password_reset_form.html'
    email_template_name = 'users/account/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    # 添加下列設置以確保使用自定義模板
    html_email_template_name = 'users/account/password_reset_email.html'
    subject_template_name = 'users/account/password_reset_subject.txt'
    
    def form_valid(self, form):
        messages.success(self.request, "密碼重設郵件已發送，請檢查您的郵箱。")
        return super().form_valid(form)

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'users/account/password_reset_done.html'

# 重設連結點開後：設定新密碼
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'users/account/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, "您的密碼已成功重設！")
        return super().form_valid(form)

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'users/account/password_reset_complete.html'    

# =====================
# 個人資料相關視圖
# =====================
class ProfileView(generic.DetailView):
    """使用者個人資料顯示頁面"""
    template_name = 'users/account/profile.html'
    
    def get_object(self):
        """獲取當前登入使用者作為資料對象"""
        return self.request.user


class ProfileEditView(generic.UpdateView):
    """使用者個人資料編輯頁面"""
    template_name = 'users/account/profile_edit.html'
    fields = ['username', 'email', 'first_name', 'last_name']  # 可根據User模型調整
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        """獲取當前登入使用者作為編輯對象"""
        return self.request.user
    
    def form_valid(self, form):
        """表單驗證成功時的處理"""
        messages.success(self.request, "個人資料已成功更新！")
        return super().form_valid(form)

