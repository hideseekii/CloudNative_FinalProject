from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from reviews.models import Review, DishReview

User = get_user_model()

class ReviewTests(TestCase):
    def setUp(self):
        # 建立測試用 user、order、orderitem、dish
        self.user = User.objects.create_user(username='testuser', password='testpass', email='user1@example.com')
        self.user2 = User.objects.create_user(username='otheruser', password='testpass', email='user2@example.com')
        self.client.force_login(self.user)
        self.client.force_login(self.user2)
        self.order = Order.objects.create(order_id=1, consumer=self.user, total_price=100.0)
        # 假設 OrderItem 有 dish 外鍵和 name_zh 欄位
        self.order_item = OrderItem.objects.create(order=self.order, dish_id=1)  # dish_id 可換成你真實 dish id

        self.client = Client()
        self.review_url = reverse('reviews:add_review', kwargs={'order_id': self.order.order_id})
        self.dish_review_url = reverse('reviews:add_dish_review', kwargs={'order_id': self.order.order_id})

    def test_add_review_not_logged_in(self):
        response = self.client.post(self.review_url, {'rating': 4, 'comment': 'Good'})
        self.assertNotEqual(response.status_code, 200)  # 應該會跳轉登入頁面

    def test_add_review_logged_in(self):
        self.client.login(username='testuser', password='testpass')

        # 新增評論
        response = self.client.post(self.review_url, {'rating': 5, 'comment': 'Excellent'})
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))

        review = Review.objects.get(user=self.user, order=self.order)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent')

    def test_update_review(self):
        Review.objects.create(user=self.user, order=self.order, rating=3, comment='Okay')

        self.client.login(username='testuser', password='testpass')
        response = self.client.post(self.review_url, {'rating': 4, 'comment': 'Better now'})
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))

        review = Review.objects.get(user=self.user, order=self.order)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Better now')

    def test_add_dish_review(self):
        self.client.login(username='testuser', password='testpass')

        # 模擬 POST 多個 dish 評論 (用 formset)
        data = {
            'form-0-rating': 5,
            'form-0-comment': 'Delicious',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
        }

        response = self.client.post(self.dish_review_url, data)
        self.assertRedirects(response, reverse('orders:order_detail', kwargs={'order_id': self.order.order_id}))

        dish_review = DishReview.objects.get(user=self.user, order_item=self.order_item)
        self.assertEqual(dish_review.rating, 5)
        self.assertEqual(dish_review.comment, 'Delicious')

    def test_review_list_view_filter_and_sort(self):
        # 建立多筆 dish review 測試過濾排序
        DishReview.objects.create(user=self.user, order_item=self.order_item, rating=5, comment='Great')
        DishReview.objects.create(user=self.user2, order_item=self.order_item, rating=3, comment='Okay')

        url = reverse('reviews:review_list')  # 請改成你 URL 名稱
        self.client.login(username='testuser', password='testpass')

        # 依 rating 過濾
        response = self.client.get(url, {'rating': '5'})
        self.assertContains(response, 'Great')
        self.assertNotContains(response, 'Okay')

        # 依 rating 降序排序
        response = self.client.get(url, {'sort': 'rating_desc'})
        self.assertEqual(response.status_code, 200)

        # 依時間升序排序
        response = self.client.get(url, {'sort': 'time_asc'})
        self.assertEqual(response.status_code, 200)
