# users/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER  = 'customer',  '顧客'
        STAFF     = 'staff',     '餐廳人員'
        ENGINEER  = 'engineer',  '工程師(後台)'

    email = models.EmailField('電子郵件', unique=True)
    role  = models.CharField(
        '身分',
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text='使用者在系統中的身分'
    )
    phone = models.CharField('聯絡電話', max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StaffProfile(models.Model):
    user    = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )

    def __str__(self):
        return f"{self.user.username} 的員工資訊"


class CustomerProfile(models.Model):
    user           = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    def __str__(self):
        return f"{self.user.username} 的顧客資訊"
