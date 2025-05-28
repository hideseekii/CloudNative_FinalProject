from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from menu.models import Dish
from orders.models import Order, OrderItem

User = get_user_model()

class OrdersTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='customer1', password='testpass', role='customer')
        self.dish1 = Dish.objects.create(name_zh='牛肉麵', price=150, is_available=True)
        self.dish2 = Dish.objects.create(name_zh='滷蛋', price=20, is_available=True)

    def test_checkout_without_login_redirects(self):
        response = self.client.post(reverse('orders:checkout'))
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, (302, 301))  # Should redirect to login

    def test_checkout_with_empty_cart_shows_error(self):
        self.client.login(username='customer1', password='testpass')
        response = self.client.post(reverse('orders:checkout'), follow=True)
        self.assertContains(response, "購物車是空的，無法結帳。")

    def test_checkout_creates_order_and_items(self):
        self.client.login(username='customer1', password='testpass')
        session = self.client.session
        session['cart'] = {
            str(self.dish1.pk): 2,
            str(self.dish2.pk): 3,
        }
        session.save()

        response = self.client.post(reverse('orders:checkout'))
        # 轉址到訂單確認頁
        order = Order.objects.filter(consumer=self.user).first()
        self.assertRedirects(response, reverse('orders:confirmation', args=[order.pk]))

        # 確認訂單資料
        self.assertEqual(order.total_price, self.dish1.price * 2 + self.dish2.price * 3)
        self.assertEqual(order.state, Order.State.UNFINISHED)
        self.assertEqual(order.items.count(), 2)

        item1 = order.items.get(dish=self.dish1)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item1.unit_price, self.dish1.price)

    def test_order_confirmation_view(self):
        order = Order.objects.create(
            consumer=self.user,
            total_price=100,
            state=Order.State.UNFINISHED
        )
        self.client.login(username='customer1', password='testpass')
        response = self.client.get(reverse('orders:confirmation', args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"訂單 #{order.order_id}")

    def test_order_detail_view_requires_login_and_ownership(self):
        order = Order.objects.create(
            consumer=self.user,
            total_price=100,
            state=Order.State.UNFINISHED
        )
        other_user = User.objects.create_user(username='other', password='testpass', role='customer')

        # 未登入應轉址
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertNotEqual(response.status_code, 200)

        # 非本人登入應 404
        self.client.login(username='other', password='testpass')
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertEqual(response.status_code, 404)

        # 本人登入可以看到訂單
        self.client.login(username='customer1', password='testpass')
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"訂單 #{order.order_id}")

    def test_order_history_view_lists_orders(self):
        # 建立多筆訂單
        Order.objects.create(consumer=self.user, total_price=100, state=Order.State.UNFINISHED)
        Order.objects.create(consumer=self.user, total_price=200, state=Order.State.FINISHED)
        other_user = User.objects.create_user(username='other', password='testpass', role='customer')
        Order.objects.create(consumer=other_user, total_price=300, state=Order.State.FINISHED)

        self.client.login(username='customer1', password='testpass')
        response = self.client.get(reverse('orders:order_history'))
        self.assertEqual(response.status_code, 200)
        # 只會看到自己的訂單
        self.assertContains(response, "訂單 #")
        orders = response.context['orders']
        self.assertEqual(len(orders), 2)
        for order in orders:
            self.assertEqual(order.consumer, self.user)
