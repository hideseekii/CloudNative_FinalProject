from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()

class StaffAccountTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='teststaff',
            email='teststaff@example.com',
            password='Password123',
            role=User.Role.STAFF
        )

    def test_signup_view(self):
        response = self.client.post(reverse('staff:signup'), {
            'username': 'newstaff',
            'email': 'newstaff@example.com',
            'password1': 'Testpass123',
            'password2': 'Testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newstaff').exists())

    def test_login_view(self):
        response = self.client.post(reverse('staff:login'), {
            'username': 'teststaff',
            'password': 'Password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertTrue(self.client.session.get('is_staff'))

    def test_logout_view(self):
        self.client.login(username='teststaff', password='Password123')
        response = self.client.post(reverse('staff:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_password_change(self):
        self.client.login(username='teststaff', password='Password123')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'Password123',
            'new_password1': 'NewPassword123',
            'new_password2': 'NewPassword123',
        })
        self.assertRedirects(response, reverse('password_change_done'))

    def test_password_reset_flow(self):
        response = self.client.post(reverse('password_reset'), {
            'email': 'teststaff@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('teststaff@example.com', mail.outbox[0].to)

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('staff:login')}?next={reverse('profile')}")

    def test_profile_view_authenticated(self):
        self.client.login(username='teststaff', password='Password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'teststaff')

    def test_profile_edit(self):
        self.client.login(username='teststaff', password='Password123')
        response = self.client.post(reverse('profile_edit'), {
            'username': 'updatedstaff',
            'email': 'updated@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        })
        self.assertRedirects(response, reverse('profile'))
        self.staff_user.refresh_from_db()
        self.assertEqual(self.staff_user.username, 'updatedstaff')
        self.assertEqual(self.staff_user.email, 'updated@example.com')
