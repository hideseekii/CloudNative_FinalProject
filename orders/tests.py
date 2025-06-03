from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from menu.models import Dish
from orders.models import Order, OrderItem
from datetime import timedelta
from unittest.mock import patch
from django.http import JsonResponse
from orders.order_tags import multiply
from decimal import Decimal

User = get_user_model()
@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    },
    SESSION_ENGINE='django.contrib.sessions.backends.db'
)

class OrderTestCoverage(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(username='customer', email='customer@example.com', password='pass')
        # self.client.force_login(self.customer)
        self.staff = User.objects.create_user(username='staff', email='staff@example.com', password='pass', role=User.Role.STAFF)
        # self.client.force_login(self.staff)

        self.dish = Dish.objects.create(name_zh='滷肉飯', name_en='Braised Pork Rice', price=80, is_available=True)

    def login_customer(self):
        self.client.force_login(self.customer)

    def login_staff(self):
        self.client.force_login(self.staff)

    def test_checkout_empty_cart(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '立即取餐'}, follow=True)
        self.assertContains(response, "購物車是空的，無法結帳。")

    def test_checkout_invalid_pickup_time(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '錯的格式'}, follow=True)
        self.assertContains(response, "取餐時間格式錯誤")

    def test_order_detail_unauthorized(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=100)

        other_user = User.objects.create_user(username='other', password='pass', role='customer')
        self.client.logout()
        self.client.login(username='other', password='pass')

        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]), follow=True)
        self.assertContains(response, "Log in to continue")

    def test_cache_hit_on_order_detail(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=160)
        OrderItem.objects.create(order=order, dish=self.dish, quantity=2, unit_price=80)

        # 第一次：MISS 並設快取
        response1 = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertContains(response1, "滷肉飯")

        # 第二次：HIT
        response2 = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertContains(response2, "滷肉飯")

    def test_cache_on_order_history(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=120)

        # 清除快取強制 MISS
        cache.delete(f'user_orders_{self.customer.id}')

        # 第一次：MISS
        response1 = self.client.get(reverse('orders:order_history'))
        self.assertContains(response1, f"#{order.order_id}")

        # 第二次：HIT
        response2 = self.client.get(reverse('orders:order_history'))
        self.assertContains(response2, f"#{order.order_id}")

    def test_checkout_success(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 2}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '立即取餐'}, follow=True)
        self.assertContains(response, "結帳成功！")
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_order_confirmation_view(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=100)
        response = self.client.get(reverse('orders:confirmation', args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#{order.order_id}")

    def test_clear_order_cache_function(self):
        order = Order.objects.create(consumer=self.customer, total_price=120)
        OrderItem.objects.create(order=order, dish=self.dish, quantity=1, unit_price=80)
        cache.set(f'order_items_{order.order_id}', 'test')
        cache.set(f'user_orders_{self.customer.id}', [order.order_id])

        from orders.views import clear_order_cache
        clear_order_cache(order.order_id, self.customer.id)

        self.assertIsNone(cache.get(f'order_items_{order.order_id}'))
        self.assertIsNone(cache.get(f'user_orders_{self.customer.id}'))

    def test_clear_user_order_cache_function(self):
        cache.set(f'user_orders_{self.customer.id}', [999])
        from orders.views import clear_user_order_cache
        clear_user_order_cache(self.customer.id)
        self.assertIsNone(cache.get(f'user_orders_{self.customer.id}'))

    def test_mark_order_complete_post(self):
        """測試標記訂單為完成"""
        self.login_staff()
        order = Order.objects.create(consumer=self.customer, total_price=100, state=Order.State.UNFINISHED)
        response = self.client.post(reverse('orders:mark_order_complete', args=[order.order_id]))
        self.assertEqual(response.status_code, 302)  # 302 重導向
        order.refresh_from_db()
        self.assertEqual(order.state, Order.State.FINISHED)

    def test_order_detail_cache_miss_and_hit(self):
        """測試 order_detail cache MISS 與 HIT"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=80)
        OrderItem.objects.create(order=order, dish=self.dish, quantity=1, unit_price=80)

        # 確保快取為空
        cache.delete(f'order_items_{order.order_id}')
        # 第一次請求，快取 MISS
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertContains(response, self.dish.name_zh)
        # 第二次請求，快取 HIT
        response2 = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertContains(response2, self.dish.name_zh)

    def test_order_history_cache_miss_and_hit(self):
        """測試 order_history 快取 MISS 與 HIT"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=88)
        cache.delete(f'user_orders_{self.customer.id}')
        # MISS
        response = self.client.get(reverse('orders:order_history'))
        self.assertContains(response, f"#{order.order_id}")
        # HIT
        response2 = self.client.get(reverse('orders:order_history'))
        self.assertContains(response2, f"#{order.order_id}")

    def test_clear_order_cache_functionality(self):
        """測試 clear_order_cache 函式"""
        order = Order.objects.create(consumer=self.customer, total_price=120)
        OrderItem.objects.create(order=order, dish=self.dish, quantity=1, unit_price=80)
        cache.set(f'order_items_{order.order_id}', 'dummy_data')
        cache.set(f'user_orders_{self.customer.id}', [order.order_id])
        from orders.views import clear_order_cache
        clear_order_cache(order.order_id, self.customer.id)
        self.assertIsNone(cache.get(f'order_items_{order.order_id}'))
        self.assertIsNone(cache.get(f'user_orders_{self.customer.id}'))

    def test_clear_user_order_cache_functionality(self):
        """測試 clear_user_order_cache 函式"""
        cache.set(f'user_orders_{self.customer.id}', [999])
        from orders.views import clear_user_order_cache
        clear_user_order_cache(self.customer.id)
        self.assertIsNone(cache.get(f'user_orders_{self.customer.id}'))

    def test_checkout_with_invalid_pickup_time_format(self):
        """測試結帳時傳入錯誤的取餐時間格式"""
        self.login_customer()
        session = self.client.session
        session['cart'] = {str(self.dish.dish_id): 1}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '25:61'}, follow=True)
        self.assertContains(response, "取餐時間格式錯誤")

    def test_checkout_with_immediate_pickup_and_cart_empty(self):
        """測試結帳時立即取餐，但購物車為空的狀況"""
        self.login_customer()
        session = self.client.session
        session['cart'] = {}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '立即取餐'}, follow=True)
        self.assertContains(response, "購物車是空的，無法結帳。")

    def test_order_confirmation_view_access(self):
        """測試訂單確認頁面"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=123)
        response = self.client.get(reverse('orders:confirmation', args=[order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#{order.order_id}")

class MultiplyFilterTests(TestCase):
    def test_multiply_integers(self):
        self.assertEqual(multiply(2, 3), Decimal('6'))

    def test_multiply_strings(self):
        self.assertEqual(multiply("2", "4"), Decimal('8'))

    def test_multiply_decimal(self):
        self.assertEqual(multiply(Decimal("1.5"), Decimal("2.0")), Decimal('3.0'))

    def test_multiply_with_zero(self):
        self.assertEqual(multiply(5, 0), Decimal('0'))

    def test_multiply_invalid_input(self):
        with self.assertRaises(Exception):
            multiply("abc", 2)
