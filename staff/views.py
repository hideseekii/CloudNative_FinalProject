from django.shortcuts import render

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
        messages.success(self.request, "員工帳號註冊成功！")
        return super().form_valid(form)

class StaffLoginView(LoginView):
    template_name = 'staff/account/login.html'

    def form_valid(self, form):
        messages.success(self.request, f"歡迎，{form.get_user().username}！")
        return super().form_valid(form)

class StaffLogoutView(LogoutView):
    next_page = reverse_lazy('staff:login')   # 登出後回 staff login
