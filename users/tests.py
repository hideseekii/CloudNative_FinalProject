# users/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()

class UserAccountTests(TestCase):
    def setUp(self):
        self.email = 'test@example.com'
        self.password = 'testpassword123'
        self.user = User.objects.create_user(
            username='testuser',
            email=self.email,
            password=self.password,
            role=User.Role.CUSTOMER
        )

    def test_customer_signup_view(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Testpass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view(self):
        response = self.client.post(reverse('login'), {
            'username': self.email,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_logout_view(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_password_change(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.post(reverse('password_change'), {
            'old_password': self.password,
            'new_password1': 'NewPass123!',
            'new_password2': 'NewPass123!',
        })
        self.assertRedirects(response, reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_password_reset(self):
        response = self.client.post(reverse('password_reset'), {
            'email': self.email
        })
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('重設密碼', mail.outbox[0].subject)

    def test_profile_view(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_profile_edit(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.post(reverse('profile_edit'), {
            'username': 'updateduser',
            'email': self.email,
            'first_name': 'Test',
            'last_name': 'User',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
