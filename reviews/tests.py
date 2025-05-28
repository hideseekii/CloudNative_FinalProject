from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from menu.models import Dish
from reviews.models import Review, DishReview

User = get_user_model()

class ReviewsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='customer1', password='testpass', role='customer')
        self.other_user = User.objects.create_user(username='other', password='testpass', role='customer')
        self.dish = Dish.objects.create(name_zh='牛肉麵', price=150, is_available=True)
        self.order = Order.objects.create(
            consumer=self.user,
            total_price=150,
            state=Order.State.UNFINISHED
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            dish=self.dish,
            quantity=1,
            unit_price=self.dish.price
        )

    def test_add_review_get_requires_login(self):
        url = reverse('reviews:add_review', args=[self.order.order_id])
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        self.client.login(username='customer1', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_review_post_creates_review(self):
        self.client.login(username='customer1', password='testpass')
        url = reverse('reviews:add_review', args=[self.order.order_id])
        data = {
            'rating': 4,
            'comment': '很好吃！',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('orders:order_detail', args=[self.order.order_id]))
        review = Review.objects.filter(user=self.user, order=self.order).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, '很好吃！')

    def test_add_review_post_updates_existing(self):
        Review.objects.create(user=self.user, order=self.order, rating=3, comment='普通')
        self.client.login(username='customer1', password='testpass')
        url = reverse('reviews:add_review', args=[self.order.order_id])
        data = {
            'rating': 5,
            'comment': '超讚！',
        }
        self.client.post(url, data)
        review = Review.objects.get(user=self.user, order=self.order)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, '超讚！')

    def test_add_dish_review_get_requires_login_and_belongs_to_user(self):
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        # not logged in
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        # login other user, should 404 since order.consumer != other_user
        self.client.login(username='other', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        # login owner
        self.client.login(username='customer1', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('dish_forms', response.context)

    def test_add_dish_review_post_creates_and_updates(self):
        self.client.login(username='customer1', password='testpass')
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])

        # POST new review for dish
        data = {
            'form-0-rating': '3',
            'form-0-comment': '還不錯',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('orders:order_detail', args=[self.order.order_id]))
        dish_review = DishReview.objects.filter(user=self.user, order_item=self.order_item).first()
        self.assertIsNotNone(dish_review)
        self.assertEqual(dish_review.rating, 3)
        self.assertEqual(dish_review.comment, '還不錯')

        # POST update the existing review
        data = {
            'form-0-rating': '5',
            'form-0-comment': '非常好吃',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(url, data)
        dish_review.refresh_from_db()
        self.assertEqual(dish_review.rating, 5)
        self.assertEqual(dish_review.comment, '非常好吃')

    def test_review_list_view_filters_and_sorts(self):
        self.client.login(username='customer1', password='testpass')

        # 建立多筆 DishReview，方便測試過濾與排序
        order2 = Order.objects.create(consumer=self.user, total_price=100, state=Order.State.FINISHED)
        order_item2 = OrderItem.objects.create(order=order2, dish=self.dish, quantity=1, unit_price=100)

        DishReview.objects.create(user=self.user, order_item=self.order_item, rating=4, comment='A')
        DishReview.objects.create(user=self.user, order_item=order_item2, rating=2, comment='B')

        url = reverse('reviews:review_list')

        # 不帶參數，預設排序（-created）
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['reviews']), 2)

        # 根據 rating 過濾
        response = self.client.get(url + '?rating=4')
        self.assertEqual(len(response.context['reviews']), 1)
        self.assertEqual(response.context['reviews'][0].rating, 4)

        # 根據 dish 名稱過濾
        response = self.client.get(url + f'?dish={self.dish.name_zh}')
        self.assertEqual(len(response.context['reviews']), 2)

        # 根據 order_id 過濾
        response = self.client.get(url + f'?order_id={self.order.order_id}')
        self.assertEqual(len(response.context['reviews']), 1)

        # 排序測試：rating_asc
        response = self.client.get(url + '?sort=rating_asc')
        ratings = [r.rating for r in response.context['reviews']]
        self.assertEqual(ratings, sorted(ratings))

        # 排序測試：rating_desc
        response = self.client.get(url + '?sort=rating_desc')
        ratings = [r.rating for r in response.context['reviews']]
        self.assertEqual(ratings, sorted(ratings, reverse=True))
