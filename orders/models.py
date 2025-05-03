# orders/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from menu.models import Dish

class Order(models.Model):
    order_id   = models.AutoField(primary_key=True)
    consumer   = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     limit_choices_to={'role': 'customer'},
                     on_delete=models.PROTECT,
                     related_name='orders'
                 )
    datetime   = models.DateTimeField('訂單時間', auto_now_add=True)

    class State(models.TextChoices):
        FINISHED    = 'finished',   '已完成'
        UNFINISHED  = 'unfinished', '未完成'

    state       = models.CharField(
                      '訂單狀態',
                      max_length=10,
                      choices=State.choices,
                      default=State.UNFINISHED
                  )
    total_price = models.DecimalField(
                      '訂單總額',
                      max_digits=10, decimal_places=2,
                      validators=[MinValueValidator(0)]
                  )

    class Meta:
        ordering = ['-datetime']
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_price__gte=0),
                name='total_price_non_negative'
            )
        ]

    def __str__(self):
        return f"{self.consumer} 的訂單 #{self.order_id} ({self.get_state_display()})"


class OrderItem(models.Model):
    item_id    = models.AutoField(primary_key=True)
    order      = models.ForeignKey(
                     Order,
                     on_delete=models.CASCADE,
                     related_name='items'
                 )
    dish       = models.ForeignKey(
                     Dish,
                     on_delete=models.PROTECT
                 )
    quantity   = models.PositiveIntegerField(
                     '點餐數量',
                     validators=[MinValueValidator(1)]
                 )
    unit_price = models.DecimalField(
                     '單價',
                     max_digits=8, decimal_places=2,
                     validators=[MinValueValidator(0)]
                 )

    class Meta:
        unique_together = ('order', 'dish')
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),
                name='quantity_positive'
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gte=0),
                name='unit_price_non_negative'
            )
        ]

    def __str__(self):
        return f"訂單 #{self.order.order_id} 的品項 {self.dish.name_zh} x{self.quantity}"


