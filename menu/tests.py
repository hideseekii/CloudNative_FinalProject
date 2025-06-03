from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from menu.models import Dish
from orders.models import Order, OrderItem
from django.core.cache import cache
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

    def test_dish_detail_view(self):
        response = self.client.get(reverse('menu:dish_detail', args=[self.dish.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.dish.name_en)


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
   
    def test_remove_nonexistent_dish_from_cart(self):
        response = self.client.get(reverse('menu:remove_from_cart', args=[9999]))
        self.assertEqual(response.status_code, 404)
    
    def test_remove_unavailable_dish_from_cart(self):
        session = self.client.session
        session['cart'] = {'999': 1}  # 不存在的 dish_id
        session.save()
        response = self.client.get(reverse('menu:remove_from_cart', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_cart_view(self):
        session = self.client.session
        session['cart'] = {str(self.dish.pk): 2}
        session.save()
        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "雞腿飯")

    def test_cart_with_deleted_dish(self):
        dish = Dish.objects.create(name_zh='要被刪', name_en='To Delete', price=50)
        session = self.client.session
        session['cart'] = {str(dish.pk): 1}
        session.save()
        dish.delete()
        response = self.client.get(reverse('menu:cart'))
        self.assertEqual(response.status_code, 200)  # 應該還是成功
        self.assertNotContains(response, 'To Delete')  # 不會顯示被刪的菜


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

    def test_checkout_with_empty_cart(self):
        session = self.client.session
        session['cart'] = {}
        session.save()
        
        response = self.client.post(reverse('menu:checkout'))
        self.assertRedirects(response, reverse('menu:cart'))


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


class DishCacheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dish = Dish.objects.create(name_zh="測試菜", name_en="Test Dish", price=100)

    def test_dish_list_cache_miss_and_hit(self):
        cache.clear()

        # 第一次請求：快取未命中
        response1 = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, "Test Dish")

        # 第二次請求：快取命中
        response2 = self.client.get(reverse('menu:dish_list'))
        self.assertEqual(response2.status_code, 200)

    def test_dish_detail_review_cache(self):
        from reviews.models import DishReview
        from orders.models import Order, OrderItem
        user = User.objects.create_user(username='reviewuser', password='pass')
        order = Order.objects.create(consumer=user, total_price=100, state=Order.State.FINISHED)
        order_item = OrderItem.objects.create(order=order, dish=self.dish, quantity=1, unit_price=100)
        DishReview.objects.create(order_item=order_item, rating=5, comment='讚')

        cache.clear()
        response = self.client.get(reverse('menu:dish_detail', args=[self.dish.pk]))
        self.assertContains(response, '讚')  # 未命中

        # 再次請求以觸發快取命中
        response2 = self.client.get(reverse('menu:dish_detail', args=[self.dish.pk]))
        self.assertEqual(response2.status_code, 200)


class DishCacheInvalidationTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='staff', password='pass', role=User.Role.STAFF)
        self.client.force_login(self.staff_user)

    def test_dish_create_clears_cache(self):
        cache.set('dish_list_all_available', ['dummy'])
        self.client.post(reverse('menu:dish_add'), {
            'name_zh': '快取測試',
            'name_en': 'Cache Test',
            'price': 100,
            'is_available': True
        })
        self.assertIsNone(cache.get('dish_list_all_available'))

    def test_dish_update_clears_cache(self):
        dish = Dish.objects.create(name_zh='原始', name_en='Original', price=50)
        cache.set(f'dish_info_{dish.pk}', 'dummy')
        self.client.post(reverse('menu:dish_edit', args=[dish.pk]), {
            'name_zh': '更新後',
            'name_en': 'Updated',
            'price': 60,
            'is_available': True
        })
        self.assertIsNone(cache.get(f'dish_info_{dish.pk}'))

    def test_dish_delete_clears_cache(self):
        dish = Dish.objects.create(name_zh='刪除測試', name_en='Delete Test', price=70)
        cache.set(f'dish_info_{dish.pk}', 'dummy')
        self.client.post(reverse('menu:dish_delete', args=[dish.pk]))
        self.assertIsNone(cache.get(f'dish_info_{dish.pk}'))

