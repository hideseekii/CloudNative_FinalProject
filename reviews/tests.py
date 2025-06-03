from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from reviews.models import Review, DishReview
from django.contrib.auth.models import User
from django.utils import timezone

User = get_user_model()

class ReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(self.user)
        self.order = Order.objects.create(order_id=123, consumer=self.user)
        self.dish = OrderItem.objects.create(order=self.order, dish_name='Test Dish', quantity=2, price=20)

    def test_add_review(self):
        """
        測試用戶是否可以對訂單新增評論
        """
        # URL 路徑設定
        url = reverse('reviews:add_review', args=[self.order.order_id])

        # 準備提交表單的數據
        data = {
            'rating': 4,
            'comment': 'Good service and great food!'
        }

        # 發送 POST 請求並檢查重定向
        response = self.client.post(url, data)

        # 檢查訂單評論是否被創建
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Good service and great food!')
        self.assertEqual(response.status_code, 302)  # 應該重定向到訂單詳情頁面

    def test_add_multiple_dish_reviews(self):
        """
        測試用戶是否可以對多個菜品新增評論
        """
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        data = {
            'form-0-rating': 5,
            'form-0-comment': 'Delicious!',
            'form-1-rating': 3,
            'form-1-comment': 'Could be better.'
        }

        response = self.client.post(url, data)

        # 檢查菜品評論是否被創建
        self.assertEqual(DishReview.objects.count(), 2)

        # 確認是否對每道菜品正確保存評論
        dish_review_1 = DishReview.objects.get(order_item=self.dish)
        self.assertEqual(dish_review_1.rating, 5)
        self.assertEqual(dish_review_1.comment, 'Delicious!')

        # 重定向到訂單詳情頁面
        self.assertEqual(response.status_code, 302)

    def test_review_list(self):
        """
        測試評論列表視圖
        """
        # 創建評論
        review = Review.objects.create(
            user=self.user,
            order=self.order,
            rating=4,
            comment='Great experience!'
        )

        url = reverse('reviews:review_list')
        response = self.client.get(url)

        # 確保返回的頁面包含我們剛創建的評論
        self.assertContains(response, review.comment)
        self.assertEqual(response.status_code, 200)

    def test_invalid_review_rating(self):
        """
        測試不合法的評論提交
        """
        url = reverse('reviews:add_review', args=[self.order.order_id])

        # 提交不合法的評分（例如超過 5 顆星）
        data = {
            'rating': 6,
            'comment': 'Too much rating!'
        }

        response = self.client.post(url, data)

        # 應該不會創建評論，並顯示表單錯誤
        self.assertEqual(Review.objects.count(), 0)
        self.assertFormError(response, 'form', 'rating', 'Ensure this value is less than or equal to 5.')

    def test_review_unique_constraint(self):
        """
        測試同一用戶對同一訂單的評論唯一性
        """
        url = reverse('reviews:add_review', args=[self.order.order_id])

        # 創建一個有效的評論
        self.client.post(url, {'rating': 4, 'comment': 'Great experience!'})

        # 嘗試創建第二次評論（應該更新而非創建新評論）
        response = self.client.post(url, {'rating': 5, 'comment': 'Excellent!'})

        # 應該只會有一個評論，且評論應該被更新
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent!')
        self.assertEqual(response.status_code, 302)  # 應該重定向

    def test_dish_review_unique_constraint(self):
        """
        測試同一用戶對同一道菜品的評論唯一性
        """
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])

        # 提交第一次菜品評論
        data = {
            'form-0-rating': 4,
            'form-0-comment': 'Tasty!'
        }
        self.client.post(url, data)

        # 嘗試提交第二次評論（應該更新而非創建新評論）
        data['form-0-rating'] = 5
        data['form-0-comment'] = 'Really tasty!'
        response = self.client.post(url, data)

        # 應該只會有一次菜品評論
        self.assertEqual(DishReview.objects.count(), 1)
        dish_review = DishReview.objects.first()
        self.assertEqual(dish_review.rating, 5)
        self.assertEqual(dish_review.comment, 'Really tasty!')
        self.assertEqual(response.status_code, 302)  # 應該重定向
