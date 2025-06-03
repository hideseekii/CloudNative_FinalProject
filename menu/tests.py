from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from menu.models import Dish
from orders.models import Order, OrderItem

class DishModelTest(TestCase):
    def test_dish_creation_and_str(self):
        dish = Dish.objects.create(name_zh="滷肉飯", price=50)
        self.assertEqual(str(dish), f"滷肉飯 (#{dish.dish_id})")
        self.assertEqual(dish.price, 50)

class DishViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dish = Dish.objects.create(name_zh="滷肉飯", price=50)

    def test_dish_list_view(self):
        response = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "滷肉飯")

    def test_dish_detail_view(self):
        response = self.client.get(reverse('menu:dish_detail', args=[self.dish.dish_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.name_zh)

class CartFunctionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.dish = Dish.objects.create(name_zh="雞排飯", price=80)

    def test_add_to_cart(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse('menu:add_to_cart', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:dish_list'))
        session = self.client.session
        self.assertIn(str(self.dish.dish_id), session.get('cart', {}))

    def test_remove_from_cart(self):
        self.client.login(username="testuser", password="password")
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 2}
        session.save()
        response = self.client.get(reverse('menu:remove_from_cart', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:cart'))
        session = self.client.session
        self.assertEqual(session['cart'][str(self.dish.dish_id)], 1)

    def test_cart_view(self):
        self.client.login(username="testuser", password="password")
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()
        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.name_zh)

class CheckoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")
        self.dish = Dish.objects.create(name_zh="牛肉麵", price=120)

    def test_checkout_process(self):
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 2}
        session.save()
        response = self.client.post(reverse('menu:checkout'))
        self.assertRedirects(response, reverse('orders:order_detail', args=[1]))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_price, 240)

class DishCRUDTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username="staff", password="password", is_staff=True)
        self.client.login(username="staff", password="password")
        self.dish = Dish.objects.create(name_zh="炸醬麵", price=70)

    def test_create_dish(self):
        response = self.client.post(reverse('menu:dish_add'), {
            'name_zh': '水餃',
            'price': 60,
            'is_available': True
        })
        self.assertRedirects(response, reverse('menu:dish_list'))
        self.assertEqual(Dish.objects.filter(name_zh="水餃").count(), 1)

    def test_update_dish(self):
        response = self.client.post(reverse('menu:dish_edit', args=[self.dish.dish_id]), {
            'name_zh': '炸醬麵升級版',
            'price': 90,
            'is_available': True
        })
        self.assertRedirects(response, reverse('menu:dish_list'))
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.name_zh, '炸醬麵升級版')

    def test_delete_dish(self):
        response = self.client.post(reverse('menu:dish_delete', args=[self.dish.dish_id]))
        self.assertRedirects(response, reverse('menu:dish_list'))
        self.assertFalse(Dish.objects.filter(dish_id=self.dish.dish_id).exists())
