# users/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()

class UserAccountTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123"
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.password,
            role=User.Role.CUSTOMER,
        )

    def test_signup_view(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPassword123',
            'password2': 'StrongPassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view(self):
        response = self.client.post(reverse('login'), {
            'username': self.user.email,
            'password': self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_logout_view(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_authenticated(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_profile_edit(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(reverse('profile_edit'), {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_password_change(self):
        self.client.login(email=self.user.email, password=self.password)
        response = self.client.post(reverse('password_change'), {
            'old_password': self.password,
            'new_password1': 'NewStrongPassword123',
            'new_password2': 'NewStrongPassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPassword123'))

    def test_password_reset(self):
        response = self.client.post(reverse('password_reset'), {
            'email': self.user.email,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("密碼重設", mail.outbox[0].subject)
