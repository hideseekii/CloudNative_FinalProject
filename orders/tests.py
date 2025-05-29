# orders/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from menu.models import Dish
from orders.models import Order, OrderItem

User = get_user_model()

class OrderTestCase(TestCase):
    def setUp(self):
        # 建立一位顧客與餐點
        self.client = Client()
        self.customer = User.objects.create_user(username='customer', password='test123')
        self.dish1 = Dish.objects.create(name_zh='炒飯', price=100, is_available=True)
        self.dish2 = Dish.objects.create(name_zh='麵線', price=50, is_available=True)

    def test_checkout_creates_order_and_items(self):
        # 登入
        self.client.login(username='customer', password='test123')
        
        # 模擬購物車
        session = self.client.session
        session['cart'] = {str(self.dish1.dish_id): 2, str(self.dish2.dish_id): 3}
        session.save()

        response = self.client.post(reverse('orders:checkout'))

        # 測試是否建立成功並重導
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)

        order = Order.objects.first()
        self.assertEqual(order.consumer, self.customer)
        self.assertEqual(float(order.total_price), 2 * 100 + 3 * 50)

        # 測試購物車是否清空
        session = self.client.session
        self.assertEqual(session.get('cart'), {})

    def test_checkout_with_empty_cart_redirects(self):
        self.client.login(username='customer', password='test123')

        session = self.client.session
        session['cart'] = {}
        session.save()

        response = self.client.post(reverse('orders:checkout'))
        self.assertRedirects(response, reverse('menu:cart'))
        self.assertEqual(Order.objects.count(), 0)

    def test_order_confirmation_view(self):
        self.client.login(username='customer', password='test123')

        order = Order.objects.create(
            consumer=self.customer,
            datetime=timezone.now(),
            state=Order.State.UNFINISHED,
            total_price=200
        )
        OrderItem.objects.create(order=order, dish=self.dish1, quantity=2, unit_price=100)

        url = reverse('orders:confirmation', args=[order.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "訂單")
        self.assertContains(response, "炒飯")

    def test_order_detail_view(self):
        self.client.login(username='customer', password='test123')

        order = Order.objects.create(
            consumer=self.customer,
            datetime=timezone.now(),
            state=Order.State.UNFINISHED,
            total_price=100
        )
        OrderItem.objects.create(order=order, dish=self.dish1, quantity=1, unit_price=100)

        url = reverse('orders:order_detail', args=[order.order_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "炒飯")
        self.assertContains(response, "100")

    def test_order_history_view(self):
        self.client.login(username='customer', password='test123')
        Order.objects.create(consumer=self.customer, total_price=120, datetime=timezone.now())
        Order.objects.create(consumer=self.customer, total_price=80, datetime=timezone.now())

        response = self.client.get(reverse('orders:order_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "訂單")
        self.assertContains(response, "120")
        self.assertContains(response, "80")
