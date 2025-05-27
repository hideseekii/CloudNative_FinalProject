# reviews/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order
from orders.models import OrderItem


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        '星等評分',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='請給 0~5 之間的整數評分'
    )
    comment = models.TextField(
        '文字評價',
        blank=True,
        help_text='可留空'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text='評論建立時間'
    )

    class Meta:
        # 一個 user 對同一筆 order 只能評價一次
        unique_together = ('user', 'order')
        # 最新的評論排前面
        ordering = ['-created']
        # 雙重保險：確保 rating 落在 0~5 之間
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=0) & models.Q(rating__lte=5),
                name='rating_between_0_and_5'
            )
        ]

    def __str__(self):
        return f"{self.user.username} 評價 訂單 #{self.order.order_id}: {self.rating} 星"

class DishReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dish_reviews'
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='dish_reviews'
    )
    rating = models.PositiveSmallIntegerField(
        '星等評分',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='請給 0~5 之間的整數評分'
    )
    comment = models.TextField(
        '文字評價',
        blank=True,
        help_text='可留空'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text='評論建立時間'
    )

    class Meta:
        unique_together = ('user', 'order_item')  # 同一使用者對同一道菜只能評一次
        ordering = ['-created']
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=0) & models.Q(rating__lte=5),
                name='dish_rating_between_0_and_5'
            )
        ]

    def __str__(self):
        return f"{self.user.username} 評價 {self.order_item.dish.name_zh}: {self.rating} 星"

'''
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order
from menu.models import Dish  # 如果菜品在 menu app 中

class DishReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dish_review'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='dish_review'
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='dish_review'
    )
    rating = models.PositiveSmallIntegerField(
        '星等評分',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='請給 0~5 之間的整數評分'
    )
    comment = models.TextField(
        '文字評價',
        blank=True,
        help_text='可留空'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text='評論建立時間'
    )

    class Meta:
        # 一個 user 對同一筆 order 只能評價一次
        unique_together = ('user', 'order')
        # 最新的評論排前面
        ordering = ['-created']
        # 雙重保險：確保 rating 落在 0~5 之間
        constraints = [
            models.CheckConstraint(
                check=models.Q(rating__gte=0) & models.Q(rating__lte=5),
                name='rating_between_0_and_5'
            )
        ]

    def __str__(self):
        return f"{self.user.username} 評價 訂單 #{self.order.order_id}: {self.rating} 星"
'''