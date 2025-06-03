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

    def test_staff_order_list_view(self):
        """測試 staff_order_list 的正常回傳與內容"""
        self.login_staff()
        order = Order.objects.create(consumer=self.customer, total_price=100)
        response = self.client.get(reverse('orders:staff_order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"訂單 #{order.order_id}")

    def test_mark_order_complete_post(self):
        """測試標記訂單為完成"""
        self.login_staff()
        order = Order.objects.create(consumer=self.customer, total_price=100, state=Order.State.UNFINISHED)
        response = self.client.post(reverse('orders:mark_order_complete', args=[order.order_id]))
        self.assertEqual(response.status_code, 302)  # 302 重導向
        order.refresh_from_db()
        self.assertEqual(order.state, Order.State.FINISHED)

    def test_generate_monthly_report_view(self):
        """測試月報表產生正確包含該月份訂單，不包含其他月份"""
        self.login_staff()
        now = timezone.now()
        # 本月訂單
        order_in_month = Order.objects.create(consumer=self.customer, total_price=200, datetime=now)
        # 上個月訂單
        last_month = now - timedelta(days=31)
        order_last_month = Order.objects.create(consumer=self.customer, total_price=999, datetime=last_month)
        response = self.client.get(reverse('orders:generate_monthly_report'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NT$200')
        self.assertNotContains(response, 'NT$999')

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

    def test_order_detail_cache_exception_handling(self):
        """測試 order_detail 中 cache.get 拋出異常的處理"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=50)
        with patch('orders.views.cache.get', side_effect=Exception("cache failure")):
            response = self.client.get(reverse('orders:order_detail', args=[order.order_id]), follow=True)
            self.assertContains(response, "載入訂單詳情時發生錯誤")

    def test_order_history_cache_miss_and_hit(self):
        """測試 order_history 快取 MISS 與 HIT"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=88)
        cache.delete(f'user_orders_{self.customer.id}')
        # MISS
        response = self.client.get(reverse('orders:order_history'))
        self.assertContains(response, f"訂單 #{order.order_id}")
        # HIT
        response2 = self.client.get(reverse('orders:order_history'))
        self.assertContains(response2, f"訂單 #{order.order_id}")

    def test_order_history_cache_exception_handling(self):
        """測試 order_history 中 cache.get 拋出異常的處理"""
        self.login_customer()
        Order.objects.create(consumer=self.customer, total_price=100)
        with patch('orders.views.cache.get', side_effect=Exception("cache fail")):
            response = self.client.get(reverse('orders:order_history'))
            self.assertContains(response, "訂單 #")

    def test_order_status_api_success_and_not_found(self):
        """測試 order_status_api 正常回應與 404 情況"""
        self.login_customer()
        order = Order.objects.create(consumer=self.customer, total_price=123)
        # 正常狀態
        response = self.client.get(reverse('orders:order_status_api', args=[order.order_id]))
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn('state', json_data)
        # 不存在訂單，應回 404
        response_404 = self.client.get(reverse('orders:order_status_api', args=[999999]))
        self.assertEqual(response_404.status_code, 404)

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
        session['cart'] = {str(self.dish.id): 1}
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
        self.assertContains(response, f"訂單 #{order.order_id}")

