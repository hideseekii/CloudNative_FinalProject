from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from menu.models import Dish
from orders.models import Order, OrderItem
from django.contrib.auth import get_user_model

User = get_user_model()

class DishViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dish = Dish.objects.create(
            name_zh="滷肉飯",
            name_en="Braised Pork Rice",
            price=50,
            is_available=True
        )
    
    def test_dish_list_view(self):
        response = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Braised Pork Rice")

class CartFunctionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_login(self.user)
        self.dish = Dish.objects.create(name_zh="雞腿飯", name_en="Chicken Rice", price=80, is_available=True)
        self.client.login(username="testuser", password="testpass")
        
    def test_add_to_cart(self):
        response = self.client.get(reverse('menu:add_to_cart', args=[self.dish.pk]))
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        cart = session.get('cart', {})
        self.assertIn(str(self.dish.pk), cart)

    def test_remove_from_cart(self):
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 1}
        session.save()
        response = self.client.get(reverse('menu:remove_from_cart', args=[self.dish.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(str(self.dish.pk), self.client.session.get('cart', {}))

    def test_cart_view(self):
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 2}
        session.save()
        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "雞腿飯")

class CheckoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="checkoutuser", password="testpass")
        self.client.force_login(self.user)
        self.dish = Dish.objects.create(
            name_zh="牛肉麵", name_en="Beef Noodles", price=120, is_available=True
        )
        self.client.login(username="checkoutuser", password="testpass")
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 1}
        session.save()

    def test_checkout_process(self):
        response = self.client.post(reverse('menu:checkout'), {
            'address': '123 TSMC Road',
            'phone': '0912345678'
        })
        self.assertEqual(response.status_code, 302)
        # You can check redirect or order created here if needed


class DishCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staff", password="staffpass", role=User.Role.STAFF
        )
        self.client.force_login(self.staff_user)

    def test_create_dish(self):
        response = self.client.post(reverse('menu:dish_add'), {
            'name_zh': '炒飯',
            'name_en': 'Fried Rice',
            'price': 90,
            'is_available': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dish.objects.filter(name_zh='炒飯').exists())

    def test_update_dish(self):
        dish = Dish.objects.create(name_zh='豆漿', name_en='Soy Milk', price=20)
        response = self.client.post(reverse('menu:dish_edit', args=[dish.pk]), {
            'name_zh': '冰豆漿',
            'name_en': 'Cold Soy Milk',
            'price': 25,
            'is_available': True
        })
        self.assertEqual(response.status_code, 302)
        dish.refresh_from_db()
        self.assertEqual(dish.name_zh, '冰豆漿')

    def test_delete_dish(self):
        dish = Dish.objects.create(name_zh='蘿蔔糕', name_en='Turnip Cake', price=30)
        response = self.client.post(reverse('menu:dish_delete', args=[dish.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Dish.objects.filter(pk=dish.pk).exists())
