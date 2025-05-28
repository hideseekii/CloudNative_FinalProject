from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from menu.models import Dish
from orders.models import Order, OrderItem
from reviews.models import DishReview

User = get_user_model()

class DishModelTest(TestCase):
    def test_dish_creation_and_str(self):
        dish = Dish.objects.create(name_zh='牛肉麵', price=120)
        self.assertEqual(str(dish), f"牛肉麵 (#{dish.dish_id})")

    def test_average_rating(self):
        user = User.objects.create_user(username='testuser', password='123', role='customer')
        dish = Dish.objects.create(name_zh='水餃', price=60)
        order = Order.objects.create(consumer=user, total_price=60)
        OrderItem.objects.create(order=order, dish=dish, quantity=1, unit_price=60)
        DishReview.objects.create(user=user, order=order, dish=dish, rating=4, comment='好吃')
        self.assertEqual(dish.average_rating(), 4.0)

class MenuViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(username='customer', password='123', role='customer')
        self.staff = User.objects.create_user(username='staff', password='123', role='staff', is_staff=True)
        self.dish = Dish.objects.create(name_zh='燒賣', price=30, is_available=True)

    def test_dish_list_public_view(self):
        response = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '燒賣')

    def test_dish_detail_view(self):
        response = self.client.get(reverse('menu:dish_detail', args=[self.dish.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '燒賣')

    def test_add_to_cart(self):
        self.client.login(username='customer', password='123')
        response = self.client.post(reverse('menu:add_to_cart', args=[self.dish.pk]))
        self.assertRedirects(response, reverse('menu:dish_list'))
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart[str(self.dish.pk)], 1)

    def test_remove_from_cart(self):
        self.client.login(username='customer', password='123')
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 2}
        session.save()

        response = self.client.post(reverse('menu:remove_from_cart', args=[self.dish.pk]))
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart[str(self.dish.pk)], 1)

    def test_cart_view(self):
        self.client.login(username='customer', password='123')
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 1}
        session.save()

        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '燒賣')

    def test_checkout_creates_order(self):
        self.client.login(username='customer', password='123')
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 2}
        session.save()

        response = self.client.post(reverse('menu:checkout'))
        self.assertRedirects(response, reverse('orders:order_detail', args=[1]))
        from orders.models import Order
        self.assertTrue(Order.objects.filter(consumer=self.customer).exists())

    def test_staff_create_view_permission(self):
        self.client.login(username='staff', password='123')
        response = self.client.get(reverse('menu:dish_add'))
        self.assertEqual(response.status_code, 200)

    def test_nonstaff_cannot_access_create(self):
        self.client.login(username='customer', password='123')
        response = self.client.get(reverse('menu:dish_add'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_dish_create_post(self):
        self.client.login(username='staff', password='123')
        data = {
            'name_zh': '炸雞',
            'price': '80',
            'is_available': True
        }
        response = self.client.post(reverse('menu:dish_add'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Dish.objects.filter(name_zh='炸雞').exists())
