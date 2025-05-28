from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UsersTests(TestCase):
    def setUp(self):
        # 建立測試使用者
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
    
    def test_signup_view_get(self):
        url = reverse('users:signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/signup.html')

    def test_signup_view_post_success(self):
        url = reverse('users:signup')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPassword123',
            'password2': 'StrongPassword123',
        }
        response = self.client.post(url, data)
        # 成功註冊會導向登入頁
        self.assertRedirects(response, reverse('users:login'))
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view(self):
        url = reverse('users:login')
        response = self.client.post(url, {
            'username': 'testuser@example.com',  # 因為 USERNAME_FIELD=email
            'password': 'password123'
        })
        self.assertRedirects(response, '/')  # 預設成功登入後導向根目錄

    def test_logout_view(self):
        self.client.login(email='testuser@example.com', password='password123')
        url = reverse('users:logout')
        response = self.client.get(url)
        self.assertRedirects(response, '/')

    def test_profile_view_requires_login(self):
        url = reverse('users:profile')
        # 未登入會導向登入頁
        response = self.client.get(url)
        self.assertRedirects(response, f'/login/?next={url}')

        # 登入後可正常訪問
        self.client.login(email='testuser@example.com', password='password123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/profile.html')

    def test_profile_edit_view(self):
        self.client.login(email='testuser@example.com', password='password123')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/account/profile_edit.html')

        # 修改資料並送出
        data = {
            'username': 'updateduser',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('users:profile'))

        # 重新從資料庫抓使用者資料檢查是否更新成功
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
