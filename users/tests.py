# users/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client

User = get_user_model()

class UserModelTests(TestCase):
    def test_user_creation(self):
        """測試用戶是否能夠正確創建"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('password123'))

class UserViewTests(TestCase):
    def setUp(self):
        """設置測試環境"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123',
            role=User.Role.CUSTOMER
        )
        self.client.force_login(self.user)

    def test_signup_page(self):
        """測試註冊頁面是否能夠正確加載"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/signup.html')
    
    def test_successful_signup(self):
        """測試成功註冊後的行為"""
        response = self.client.post(reverse('signup'), {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # 預期重定向至登入頁面
        self.assertRedirects(response, reverse('login'))
        # 檢查消息
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "帳號註冊成功！現在您可以登入。")
        # self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_page(self):
        """測試登入頁面是否能夠正確加載"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/login.html')

    def test_successful_login(self):
        """測試成功登入後的行為"""
        response = self.client.post(reverse('login'), {
            'username': 'newuser@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # 預期重定向至首頁
        # self.assertRedirects(response, reverse('home'))  # 根據你的首頁 URL 修改
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_logout(self):
        """測試登出功能"""
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        # 檢查消息
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "您已成功登出。")

    def test_password_change(self):
        """測試密碼變更功能"""
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/password_change_form.html')

        response = self.client.post(reverse('password_change'), {
            'old_password': 'password123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })
        self.assertRedirects(response, reverse('password_change_done'))
        # 檢查消息
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "您的密碼已成功變更！")

    def test_password_reset(self):
        """測試密碼重設流程"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/password_reset_form.html')

        # 模擬密碼重設
        response = self.client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })
        self.assertRedirects(response, reverse('password_reset_done'))
        # 檢查郵件是否發送
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_view(self):
        """測試個人資料顯示頁面"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/profile.html')
        self.assertContains(response, self.user.username)

    def test_profile_edit(self):
        """測試個人資料編輯頁面"""
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/profile_edit.html')

        response = self.client.post(reverse('profile_edit'), {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'First',
            'last_name': 'Last'
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()  # 重新載入用戶資料
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')

