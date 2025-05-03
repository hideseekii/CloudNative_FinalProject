# reviews/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from orders.models import Order


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
