# users/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import CustomerProfile, StaffProfile

User = get_user_model()

class CustomerSignUpForm(forms.ModelForm):
    password = forms.CharField(label="密碼", widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['email', 'username', 'phone']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.CUSTOMER
        if commit:
            user.save()
            CustomerProfile.objects.create(user=user)
        return user


class StaffSignUpForm(forms.ModelForm):
    password    = forms.CharField(label="密碼", widget=forms.PasswordInput)
    invite_code = forms.CharField(label="邀請碼")
    class Meta:
        model = User
        fields = ['email', 'username', 'phone', 'invite_code']

    def clean_invite_code(self):
        code = self.cleaned_data['invite_code']
        if not Invitation.objects.filter(code=code, valid=True).exists():
            raise forms.ValidationError("邀請碼無效")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.Role.STAFF
        if commit:
            user.save()
            StaffProfile.objects.create(user=user)
            # 將邀請碼標記使用過
            Invitation.objects.filter(code=self.cleaned_data['invite_code']).update(valid=False)
        return user
