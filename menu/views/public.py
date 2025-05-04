# menu/views/public.py
from django.db.models import Q
from django.views.generic import ListView, DetailView
from menu.models import Dish

class DishListView(ListView):
    model = Dish
    template_name = 'menu/public/dish_list.html'
    context_object_name = 'dishes'

    def get_queryset(self):
        qs = Dish.objects.filter(is_available=True)
        q = self.request.GET.get('q', '').strip()
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if q:
            qs = qs.filter(
                Q(name_zh__icontains=q) |
                Q(name_en__icontains=q) |
                Q(description_zh__icontains=q) |
                Q(description_en__icontains=q)
            )
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs

class DishDetailView(DetailView):
    model = Dish
    template_name = 'menu/public/dish_detail.html'
    context_object_name = 'dish'
