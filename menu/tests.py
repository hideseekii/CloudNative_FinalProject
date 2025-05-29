from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from menu.models import Dish
from orders.models import Order

User = get_user_model()

class MenuViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)

        self.dish = Dish.objects.create(name_zh='牛肉麵', price=150, is_available=True)

    def test_add_to_cart(self):
        response = self.client.post(reverse('menu:add_to_cart', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:dish_list'))

    def test_cart_view(self):
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()

        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)

    def test_remove_from_cart(self):
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()

        response = self.client.post(reverse('menu:remove_from_cart', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:cart'))

    def test_checkout(self):
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()

        response = self.client.post(reverse('menu:checkout'))
        self.assertEqual(Order.objects.count(), 1)


class StaffViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staffuser', password='password', is_staff=True)
        self.client.force_login(self.staff_user)

        self.dish = Dish.objects.create(name_zh='炒飯', price=100, is_available=True)
        self.dish.refresh_from_db()

    def test_create_dish_view(self):
        response = self.client.post(reverse('menu:dish_add'), {
            'name_zh': '新菜',
            'name_en': 'New Dish',
            'description_zh': '這是一道好菜',
            'price': 200,
            'image_url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShd8TUTO_NJVwtZfU41VYhJox8-72OH60YMw&s',
            'is_available': True,
        })
        self.assertEqual(response.status_code, 302)

    def test_update_dish_view(self):
        response = self.client.post(reverse('menu:dish_edit', args=[self.dish.dish_id]), {
            'name_zh': '改過的炒飯',
            'price': 120,
            'is_available': True,
        })
        self.assertRedirects(response, reverse('menu:dish_list'))

    def test_delete_dish_view(self):
        response = self.client.post(reverse('menu:dish_delete', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:dish_list'))
