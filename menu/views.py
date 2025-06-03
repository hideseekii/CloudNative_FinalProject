# menu/views.py - Redis 優化版本
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from django.core.cache import cache,caches  # 新增 Redis 快取
import hashlib  # 用於生成快取鍵
from django.views.decorators.cache import never_cache
from .models import Dish
from .utils import get_pickup_times
from orders.models import Order, OrderItem
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Dish
from common.mixins import StaffRequiredMixin
from django.urls import reverse_lazy
from reviews.models import DishReview
from orders.models import OrderItem
from django.utils.decorators import method_decorator

@method_decorator(never_cache, name='dispatch')
class DishListView(ListView):
    model = Dish
    template_name = 'menu/dish_list.html'
    context_object_name = 'dishes'
    paginate_by = None

    def get_queryset(self):
        # 取得查詢參數
        q = self.request.GET.get('q', '').strip()
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        # ✅ 無搜尋參數：回傳所有菜品（含下架）快取
        if not q and not min_price and not max_price:
            cache_key = 'dish_list_all'
            dishes = cache.get(cache_key)

            if dishes is None:
                print("🔴 Cache MISS: 全部菜單")
                dishes = list(Dish.objects.all())
                cache.set(cache_key, dishes, 1)  # 快取 15 分鐘
            else:
                print("🟢 Cache HIT: 全部菜單")

            return dishes  # ✅ 已是 Dish instance，可直接回傳

        # ✅ 有搜尋參數：查詢篩選結果（可視需求保留 is_available 條件）
        else:
            search_params = f"{q}_{min_price}_{max_price}"
            cache_key = f"dish_search_{hashlib.md5(search_params.encode()).hexdigest()}"
            dish_ids = cache.get(cache_key)

            if dish_ids is None:
                print(f"🔴 Cache MISS: 搜尋 {search_params}")
                qs = Dish.objects.all()  # ✅ 包含所有菜，若想要僅上架改這行

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

                dish_ids = list(qs.values_list('dish_id', flat=True))
                cache.set(cache_key, dish_ids, 1)  # 快取 5 分鐘
            else:
                print(f"🟢 Cache HIT: 搜尋 {search_params}")

            return Dish.objects.filter(dish_id__in=dish_ids)

class DishDetailView(DetailView):
    model = Dish
    template_name = 'menu/dish_detail.html'
    context_object_name = 'dish'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dish = self.object
        
        # 快取菜品評論
        cache_key = f'dish_reviews_{dish.dish_id}'
        related_reviews = cache.get(cache_key)
        
        if related_reviews is None:
            print(f"🔴 Cache MISS: 菜品 {dish.dish_id} 的評論")
            related_reviews = list(
                DishReview.objects.filter(order_item__dish=dish)
                .distinct()
                .order_by('-created')
                .values(
                    'order_item__dish__dish_id', 'rating', 'comment', 'created'
                )
            )
            # 快取 10 分鐘
            cache.set(cache_key, related_reviews, 1)
        else:
            print(f"🟢 Cache HIT: 菜品 {dish.dish_id} 的評論")
        
        context['related_reviews'] = related_reviews
        return context

@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    if cart:
        # 批次查詢所有需要的菜品（減少資料庫查詢次數）
        dish_ids = [int(dish_id) for dish_id in cart.keys()]
        
        # 嘗試從快取取得菜品資訊
        cached_dishes = {}
        cache_keys = [f'dish_info_{dish_id}' for dish_id in dish_ids]
        cached_data = cache.get_many(cache_keys)
        
        # 整理已快取的菜品
        for cache_key, dish_data in cached_data.items():
            dish_id = int(cache_key.split('_')[-1])
            cached_dishes[dish_id] = dish_data
        
        # 查詢未快取的菜品
        uncached_dish_ids = [dish_id for dish_id in dish_ids if dish_id not in cached_dishes]
        
        if uncached_dish_ids:
            print(f"🔴 Cache MISS: 查詢菜品 {uncached_dish_ids}")
            uncached_dishes = Dish.objects.filter(dish_id__in=uncached_dish_ids).values(
                'dish_id', 'name_zh', 'price', 'is_available'
            )
            
            # 將新查詢的菜品加入快取
            cache_data = {}
            for dish in uncached_dishes:
                cache_key = f"dish_info_{dish['dish_id']}"
                cache_data[cache_key] = dish
                cached_dishes[dish['dish_id']] = dish
            
            # 批次設定快取（10分鐘）
            cache.set_many(cache_data, 1)
        else:
            print("🟢 Cache HIT: 所有購物車菜品都有快取")
        
        # 計算購物車項目
        for dish_id, quantity in cart.items():
            dish_id = int(dish_id)
            if dish_id in cached_dishes:
                dish_data = cached_dishes[dish_id]
                if dish_data['is_available']:  # 確保菜品仍然可用
                    subtotal = dish_data['price'] * quantity
                    total_price += subtotal
                    cart_items.append({
                        'dish': dish_data,  # 使用快取的資料
                        'quantity': quantity,
                        'subtotal': subtotal
                    })
            else:
                # 菜品已被刪除，從購物車移除
                del cart[str(dish_id)]
                request.session['cart'] = cart
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    
    return render(request, 'menu/cart.html', context)

# === 快取失效處理 ===
# 在 Staff 的 Create/Update/Delete Views 中加入快取清除
@method_decorator(never_cache, name='dispatch')
class DishCreateView(StaffRequiredMixin, CreateView):
    model = Dish
    fields = ['name_zh','name_en','description_zh','price','image_url','is_available']
    template_name = 'menu/dish_form.html'
    success_url = reverse_lazy('menu:dish_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # 清除相關快取
        self._clear_dish_cache()
        return response
    
    def _clear_dish_cache(self):
        """清除菜品相關的快取"""
        cache.delete('dish_list_all_available')
        # 清除所有搜尋快取（使用模式匹配）
        cache.delete_pattern('dish_search_*')
        print("🧹 已清除菜品列表快取")

@method_decorator(never_cache, name='dispatch')
class DishUpdateView(StaffRequiredMixin, UpdateView):
    model = Dish
    fields = ['name_zh','name_en','description_zh','price','image_url','is_available']
    template_name = 'menu/dish_form.html'
    success_url = reverse_lazy('menu:dish_list')


    def form_valid(self, form):
        response = super().form_valid(form)
        # 清除相關快取
        dish_id = self.object.dish_id
        cache.delete(f'dish_info_{dish_id}')
        cache.delete(f'dish_reviews_{dish_id}')
        cache.delete('dish_list_all_available')
        cache.delete_pattern('dish_search_*')
        print(f"🧹 已清除菜品 {dish_id} 相關快取")
        return response

@method_decorator(never_cache, name='dispatch')
class DishDeleteView(StaffRequiredMixin, DeleteView):
    model = Dish
    template_name = 'menu/dish_confirm_delete.html'
    success_url = '/menu/dishes/'
    print("🎯 正在使用 Redis 嗎？", caches['default'].__class__)
    def delete(self, request, *args, **kwargs):
        dish_id = self.get_object().dish_id
        response = super().delete(request, *args, **kwargs)
        # 清除相關快取
        cache.delete(f'dish_info_{dish_id}')
        cache.delete(f'dish_reviews_{dish_id}')
        cache.delete('dish_list_all_available')

        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        keys = redis_conn.keys("cloudnative_final:dish_search_*")
        if keys:
            redis_conn.delete(*keys)
            print(f"🧹 已刪除 {len(keys)} 個 dish_search_* 快取")
        print("✅ 刪除快取成功")
        return response

# === 其他不變的 views ===
@login_required
def add_to_cart(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    
    # 獲取或創建購物車
    cart = request.session.get('cart', {})
    
    # 將菜品 ID 轉換為字符串作為字典鍵
    dish_id = str(dish.dish_id)
    
    # 添加或增加購物車中的商品數量
    if dish_id in cart:
        cart[dish_id] += 1
    else:
        cart[dish_id] = 1
    
    # 保存購物車
    request.session['cart'] = cart
    
    messages.success(request, f"已將 {dish.name_zh} 加入購物車")
    return redirect('menu:dish_list')

@login_required
def remove_from_cart(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    
    # 獲取購物車
    cart = request.session.get('cart', {})
    
    # 將菜品 ID 轉換為字符串
    dish_id = str(dish.dish_id)
    
    # 減少或移除購物車中的商品
    if dish_id in cart:
        if cart[dish_id] > 1:
            cart[dish_id] -= 1
        else:
            del cart[dish_id]
        
        # 保存購物車
        request.session['cart'] = cart
        messages.info(request, f"已從購物車移除 {dish.name_zh}")
    
    return redirect('menu:cart')

@login_required

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    if cart:
        for dish_id, quantity in cart.items():
            try:
                dish = Dish.objects.get(dish_id=int(dish_id))
                subtotal = dish.price * quantity
                total_price += subtotal
                cart_items.append({
                    'dish': dish,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            except Dish.DoesNotExist:
                del cart[dish_id]
                request.session['cart'] = cart

    # 加入 pickup_times
    pickup_times = get_pickup_times()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'pickup_times': pickup_times,  # 加這行
    }

    return render(request, 'menu/cart.html', context)


@login_required


@transaction.atomic
def checkout(request):
    # Get cart contents
    cart = request.session.get('cart', {})
    
    # Check if cart is empty
    if not cart:
        messages.warning(request, "您的購物車是空的，請先添加商品。")
        return redirect('menu:cart')
    
    # Calculate total and prepare items
    cart_items = []
    total_price = Decimal('0.00')
    
    for dish_id, quantity in cart.items():
        try:
            dish = Dish.objects.get(dish_id=int(dish_id))
            subtotal = dish.price * quantity
            total_price += subtotal
            cart_items.append({
                'dish': dish,
                'quantity': quantity,
                'subtotal': subtotal
            })
        except Dish.DoesNotExist:
            continue
    
    # Create order
    order = Order.objects.create(
        consumer=request.user,
        total_price=total_price,
        state=Order.State.UNFINISHED
    )
    
    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            dish=item['dish'],
            quantity=item['quantity'],
            unit_price=item['dish'].price
        )
    
    # Clear cart
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, f"訂單已成功創建，訂單編號: #{order.order_id}")
    return redirect('orders:order_detail', order_id=order.order_id)