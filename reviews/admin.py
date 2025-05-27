from django.contrib import admin

# Register your models here.

from .models import Review, DishReview

admin.site.register(Review)

admin.site.register(DishReview)  



'''
from .models import DishReview

@admin.register(DishReview)
class DishReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'dish', 'order', 'rating', 'created')
    list_filter = ('rating', 'created')
    search_fields = ('user__username', 'dish__name_zh', 'comment')
'''

