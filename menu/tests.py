from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Dish
from orders.models import Order, OrderItem

User = get_user_model()

class DishModelTest(TestCase):
    def setUp(self):
        self.dish = Dish.objects.create(
            name_zh='紅燒牛肉麵',
            name_en='Braised Beef Noodles',
            description_zh='經典牛肉湯麵',
            price=150.00,
            is_available=True
        )

    def test_dish_str(self):
        self.assertEqual(str(self.dish), f"{self.dish.name_zh} (#{self.dish.dish_id})")


class MenuViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

        self.dish = Dish.objects.create(
            name_zh='紅燒牛肉麵',
            name_en='Beef Noodle',
            description_zh='好吃的牛肉麵',
            price=100,
            is_available=True
        )

    def test_dish_list_view(self):
        response = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.name_zh)

    def test_dish_detail_view(self):
        response = self.client.get(reverse('menu:dish_detail', args=[self.dish.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.description_zh)

    def test_add_to_cart(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('menu:add_to_cart', args=[self.dish.pk]))
        self.assertRedirects(response, reverse('menu:dish_list'))
        session = self.client.session
        self.assertIn(str(self.dish.pk), session['cart'])

    def test_remove_from_cart(self):
        self.client.login(username='testuser', password='password')
        # Add item first
        self.client.get(reverse('menu:add_to_cart', args=[self.dish.pk]))
        response = self.client.get(reverse('menu:remove_from_cart', args=[self.dish.pk]))
        self.assertRedirects(response, reverse('menu:cart'))

    def test_cart_view(self):
        self.client.login(username='testuser', password='password')
        self.client.get(reverse('menu:add_to_cart', args=[self.dish.pk]))
        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.name_zh)

    def test_checkout(self):
        self.client.login(username='testuser', password='password')
        self.client.get(reverse('menu:add_to_cart', args=[self.dish.pk]))
        response = self.client.post(reverse('menu:checkout'))
        self.assertEqual(response.status_code, 302)  # Redirect to order detail
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)


class StaffViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff', password='password', is_staff=True
        )
        self.client.login(username='staff', password='password')

        self.dish = Dish.objects.create(
            name_zh='蔥油餅',
            price=50,
            is_available=True
        )

    def test_create_dish_view(self):
        self.client.login(username='staff', password='password')
        response = self.client.post(reverse('menu:dish_add'), {
            'name_zh': '糖醋排骨',
            'price': 120,
            'is_available': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dish.objects.filter(name_zh='糖醋排骨').exists())

    def test_update_dish_view(self):
        self.client.login(username='staff', password='password')
        response = self.client.post(reverse('menu:dish_edit', args=[self.dish.pk]), {
            'name_zh': '更新後蔥油餅',
            'price': 60,
            'is_available': True
        })
        self.assertRedirects(response, '/menu/dishes/')
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.name_zh, '更新後蔥油餅')

    def test_delete_dish_view(self):
        self.client.login(username='staff', password='password')
        response = self.client.post(reverse('menu:dish_delete', args=[self.dish.pk]))
        self.assertRedirects(response, '/menu/dishes/')
        self.assertFalse(Dish.objects.filter(pk=self.dish.pk).exists())
