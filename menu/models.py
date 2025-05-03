# menu/models.py
from django.db import models
from django.core.validators import MinValueValidator

class Dish(models.Model):
    dish_id         = models.AutoField(primary_key=True)
    name_zh         = models.CharField('菜名（中文）', max_length=100)
    name_en         = models.CharField('菜名（英文）', max_length=100, blank=True)
    description_zh  = models.TextField('菜品描述（中文）', blank=True)
    description_en  = models.TextField('菜品描述（英文）', blank=True)
    price           = models.DecimalField(
                         '菜品價格',
                         max_digits=8, decimal_places=2,
                         validators=[MinValueValidator(0)]
                      )
    image_url       = models.URLField('圖片 URL', max_length=255, blank=True)
    is_available    = models.BooleanField('是否上架中', default=True)

    class Meta:
        ordering = ['dish_id']

    def __str__(self):
        return f"{self.name_zh} (#{self.dish_id})"
