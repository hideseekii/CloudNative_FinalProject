from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from menu.models import Dish
from orders.models import Order, OrderItem
from reviews.models import Review, DishReview
from django.utils import timezone

User = get_user_model()

class ReviewTests(TestCase):
    def setUp(self):
        # 建立使用者
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_login(self.user)

        # 建立訂單與訂單項目
        self.dish = Dish.objects.create(name_zh='牛肉麵', price=150, is_available=True)
        self.order = Order.objects.create(order_id=1, consumer=self.user, total_price=150.0)
        self.order_item = OrderItem.objects.create(item_id=1, order=self.order, dish=self.dish, quantity=1, unit_price=150)

    def test_add_review_create_and_update(self):
        url = reverse('reviews:add_review', kwargs={'order_id': self.order.order_id})

        # 新增評論
        response = self.client.post(url, data={
            'rating': 4,
            'comment': '不錯的服務'
        })
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))
        review = Review.objects.get(user=self.user, order=self.order)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, '不錯的服務')

        # 更新評論
        response = self.client.post(url, data={
            'rating': 5,
            'comment': '服務很好！'
        })
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, '服務很好！')

    def test_add_dish_review_create_and_update(self):
        url = reverse('reviews:add_dish_review', kwargs={'order_id': self.order.order_id})

        # 先建立 formset 要的資料，只有一個菜品
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-rating': '3',
            'form-0-comment': '普通口味',
        }
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))
        dish_review = DishReview.objects.get(user=self.user, order_item=self.order_item)
        self.assertEqual(dish_review.rating, 3)
        self.assertEqual(dish_review.comment, '普通口味')

        # 更新評論
        data['form-0-rating'] = '5'
        data['form-0-comment'] = '非常好吃！'
        data['form-INITIAL_FORMS'] = '1'  # 告訴 formset 有初始表單
        response = self.client.post(url, data=data)
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))
        dish_review.refresh_from_db()
        self.assertEqual(dish_review.rating, 5)
        self.assertEqual(dish_review.comment, '非常好吃！')

    def test_review_list_view_filter_sort(self):
        # 建立一些 DishReview 資料
        dish2 = Dish.objects.create(name_zh='炒麵', price=200, is_available=True)
        item2 = OrderItem.objects.create(item_id=2, order=self.order, dish=dish2, quantity=1, unit_price=200)
        DishReview.objects.create(user=self.user, order_item=self.order_item, rating=4, comment='好吃', created=timezone.now())
        DishReview.objects.create(user=self.user, order_item=item2, rating=2, comment='普通', created=timezone.now())

        url = reverse('reviews:review_list')

        # 篩選 dish name (假設 dish.name_zh 為空，先直接測 rating 篩選)
        response = self.client.get(url, {'rating': '4'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '好吃')
        self.assertNotContains(response, '普通')

        # 排序測試
        response = self.client.get(url, {'sort': 'rating_asc'})
        self.assertEqual(response.status_code, 200)
        reviews = response.context['reviews']
        ratings = [r.rating for r in reviews]
        self.assertEqual(ratings, sorted(ratings))  # 確保排序由小到大

        response = self.client.get(url, {'sort': 'rating_desc'})
        reviews = response.context['reviews']
        ratings_desc = [r.rating for r in reviews]
        self.assertEqual(ratings_desc, sorted(ratings_desc, reverse=True))  # 由大到小

