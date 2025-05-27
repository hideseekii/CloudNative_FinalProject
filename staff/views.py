from django.shortcuts import render
from django.contrib.auth import views as auth_views
# Create your views here.
# staff/views.py
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView

from .forms import StaffSignUpForm

class StaffSignUpView(generic.CreateView):
    form_class    = StaffSignUpForm
    template_name = 'staff/account/signup.html'
    success_url   = reverse_lazy('staff:login')
    
    def form_valid(self, form):
        messages.success(self.request, "staff signup successfully")
        return super().form_valid(form)

class StaffLoginView(LoginView):
    template_name = 'staff/account/login.html'

    def form_valid(self, form):
        user = form.get_user()
        self.request.session['is_staff'] = True
        messages.success(self.request, f"wellcomes，{form.get_user().username}！")
        return super().form_valid(form)

class StaffLogoutView(LogoutView):
    next_page = reverse_lazy('staff:login')   # 登出後回 staff login
    
    def dispatch(self, request, *args, **kwargs):
        # 清除 is_staff session 記錄
        request.session.pop('is_staff', None)

        messages.success(request, "您已成功登出")
        return super().dispatch(request, *args, **kwargs)


# 密碼變更
class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'staff/account/password_change_form.html'
    success_url = reverse_lazy('password_change_done')
    
    def form_valid(self, form):
        messages.success(self.request, "您的密碼已成功變更！")
        return super().form_valid(form)

class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'staff/account/password_change_done.html'

# 密碼重設：輸入 email
class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'staff/account/password_reset_form.html'
    email_template_name = 'staff/account/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    # 添加下列設置以確保使用自定義模板
    html_email_template_name = 'staff/account/password_reset_email.html'
    subject_template_name = 'staff/account/password_reset_subject.txt'
    
    def form_valid(self, form):
        messages.success(self.request, "密碼重設郵件已發送，請檢查您的郵箱。")
        return super().form_valid(form)

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'staff/account/password_reset_done.html'

# 重設連結點開後：設定新密碼
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'staff/account/password_reset_confirm.html'
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
    template_name = 'staff/account/profile.html'
    
    def get_object(self):
        """獲取當前登入使用者作為資料對象"""
        return self.request.user


class ProfileEditView(generic.UpdateView):
    """使用者個人資料編輯頁面"""
    template_name = 'staff/account/profile_edit.html'
    fields = ['username', 'email', 'first_name', 'last_name']  # 可根據User模型調整
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        """獲取當前登入使用者作為編輯對象"""
        return self.request.user
    
    def form_valid(self, form):
        """表單驗證成功時的處理"""
        messages.success(self.request, "個人資料已成功更新！")
        return super().form_valid(form)

