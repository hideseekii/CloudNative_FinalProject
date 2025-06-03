from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from menu.models import Dish
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
        self.the_dish = Dish.objects.create(name_zh='牛肉麵', price=150, is_available=True)
        self.order = Order.objects.create(order_id=123, consumer=self.user, total_price=100)
        self.dish = OrderItem.objects.create(item_id=1, order=self.order, dish=self.the_dish, quantity=1, unit_price=150)

    def test_get_add_review_empty_form(self):
        # 尚未有評論紀錄時 GET 應提供空表單
        url = reverse('reviews:add_review', args=[self.order.order_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertContains(response, '<form')

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

    def test_get_add_review_prefilled_form(self):
        # 先建立評論
        Review.objects.create(user=self.user, order=self.order, rating=3, comment='Nice')

        url = reverse('reviews:add_review', args=[self.order.order_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertContains(response, 'Nice')

    def test_get_add_dish_review_empty_form(self):
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')
        self.assertEqual(len(response.context['formset'].forms), 1)

    def test_get_add_dish_review_with_existing_data(self):
        DishReview.objects.create(user=self.user, order_item=self.dish, rating=3, comment='Okay')

        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Okay')
    
    def test_add_multiple_dish_reviews(self):
        """
        測試用戶是否可以對多個菜品新增評論
        """
        second_dish = Dish.objects.create(name_zh='滷肉飯', price=100, is_available=True)
        second_order_item = OrderItem.objects.create(item_id=2, order=self.order, dish=second_dish, quantity=1, unit_price=100)
        
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-order_item': str(self.dish.item_id),
            'form-0-rating': 5,
            'form-0-comment': 'Delicious!',

            'form-1-order_item': str(second_order_item.item_id),
            'form-1-rating': 3,
            'form-1-comment': 'Could be better.'
        }

        response = self.client.post(url, data)

        self.assertEqual(DishReview.objects.count(), 2)

        # 驗證第一筆評論
        dish_review_1 = DishReview.objects.get(order_item=self.dish)
        self.assertEqual(dish_review_1.rating, 5)
        self.assertEqual(dish_review_1.comment, 'Delicious!')

        self.assertEqual(response.status_code, 302)

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

        self.assertEqual(response.status_code, 200)  # 頁面應該不重定向
        self.assertEqual(Review.objects.count(), 0)

        # 從 context 抓取表單物件
        form = response.context['form']
        self.assertFormError(form, 'rating', 'Ensure this value is less than or equal to 5.')

    def test_invalid_dish_review_submission(self):
        url = reverse('reviews:add_dish_review', args=[self.order.order_id])
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-order_item': str(self.dish.pk),  # note: this is not actually used by form
            'form-0-rating': 6,  # invalid
            'form-0-comment': 'Too much stars!'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DishReview.objects.count(), 0)
    
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
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-order_item': str(self.dish.pk),
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
