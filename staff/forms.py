# staff/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User

class StaffSignUpForm(UserCreationForm):
    """
    員工註冊表單：只要 username, email, password，
    並在 save() 時把 role 設為 staff。
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STAFF
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label="帳號")
    password = forms.CharField(widget=forms.PasswordInput, label="密碼")