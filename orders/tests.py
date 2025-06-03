from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from menu.models import Dish
from orders.models import Order, OrderItem
from datetime import timedelta
from unittest.mock import patch

User = get_user_model()

class OrderTestCoverage(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(username='customer', password='pass')
        # self.client.force_login(self.customer)
        self.staff = User.objects.create_user(username='staff', password='pass', role=User.Role.STAFF)
        # self.client.force_login(self.staff)

        self.dish = Dish.objects.create(name_zh='滷肉飯', name_en='Braised Pork Rice', price=80, is_available=True)

    def login_customer(self):
        self.client.login(username='customer', password='pass')

    def login_staff(self):
        self.client.login(username='staff', password='pass')

    def test_checkout_empty_cart(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {'pickup_time': '立即取餐'}, follow=True)
        self.assertContains(response, "購物車是空的")

    def test_checkout_invalid_pickup_time(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {str(self.dish.id): 1}
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
        self.assertContains(response, "載入訂單詳情時發生錯誤")

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
        self.assertContains(response1, f"訂單 #{order.order_id}")

        # 第二次：HIT
        response2 = self.client.get(reverse('orders:order_history'))
        self.assertContains(response2, f"訂單 #{order.order_id}")

    def test_order_status_api_error(self):
        self.login_customer()
        response = self.client.get(reverse('orders:order_status_api', args=[999]))  # 不存在
        self.assertEqual(response.status_code, 404)

    def test_staff_order_list_and_complete(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=200)
        self.client.logout()

        self.login_staff()
        # 確認訂單在列表中
        response = self.client.get(reverse('orders:staff_order_list'))
        self.assertContains(response, f"訂單 #{order.order_id}")

        # 標記完成
        response = self.client.post(reverse('orders:mark_order_complete', args=[order.order_id]), follow=True)
        self.assertRedirects(response, reverse('orders:staff_order_list'))

        order.refresh_from_db()
        self.assertEqual(order.state, Order.State.FINISHED)

    def test_monthly_report_boundaries(self):
        self.login_staff()
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = start_of_month - timedelta(days=1)

        # 應該出現在報表中
        Order.objects.create(consumer=self.customer, total_price=150, datetime=now)
        # 不應出現在報表中
        Order.objects.create(consumer=self.customer, total_price=999, datetime=last_month)

        response = self.client.get(reverse('orders:generate_monthly_report'))
        self.assertContains(response, 'NT$150')
        self.assertNotContains(response, 'NT$999')

    def test_checkout_success(self):
        self.login_customer()
        session = self.client.session
        session['cart'] = {str(self.dish.id): 2}
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
        self.assertContains(response, f"訂單 #{order.order_id}")

    def test_order_status_api_success(self):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=300)
        response = self.client.get(reverse('orders:order_status_api', args=[order.order_id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('state', response.json())

    @patch('orders.views.cache.get', side_effect=Exception("Cache error"))
    def test_order_detail_cache_exception(self, mock_cache):
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=50)
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]), follow=True)
        self.assertContains(response, "載入訂單詳情時發生錯誤")

    @patch('orders.views.cache.get', side_effect=Exception("Cache error"))
    def test_order_history_cache_exception(self, mock_cache):
        self.login_customer()
        Order.objects.create(consumer=self.customer, total_price=88)
        response = self.client.get(reverse('orders:order_history'))
        self.assertContains(response, "訂單 #")

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

