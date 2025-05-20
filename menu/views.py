# menu/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal


from .models import Dish
from orders.models import Order, OrderItem


# for staff import
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Dish
from common.mixins import StaffRequiredMixin
from django.urls import reverse_lazy

# 公開區域視圖
class DishListView(ListView):
    model = Dish
    template_name = 'menu/dish_list.html'
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
    template_name = 'menu/dish_detail.html'
    context_object_name = 'dish'

# 購物車視圖
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
    # 獲取購物車內容
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    # 如果購物車不為空，獲取菜品詳情
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
                # 如果菜品已被刪除，從購物車中移除
                del cart[dish_id]
                request.session['cart'] = cart
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price
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


# 給staff 的新增刪除
class DishListView(ListView):
    model = Dish
    template_name = 'menu/dish_list.html'
    context_object_name = 'dishes'  

class DishCreateView(StaffRequiredMixin, CreateView):
    model = Dish
    fields = ['name_zh','name_en','description_zh','price','image_url','is_available']
    template_name = 'menu/dish_form.html'
    # success_url = '/menu/dishes/'
    success_url = reverse_lazy('menu:dish_list')

    def form_invalid(self, form):
        # 在 console 打印所有字段错误
        print("Form is invalid:", form.errors.as_json())
        return super().form_invalid(form)

class DishUpdateView(StaffRequiredMixin, UpdateView):
    model = Dish
    fields = ['name_zh','name_en','description_zh','price','image_url','is_available']
    template_name = 'menu/dish_form.html'
    success_url = '/menu/dishes/'

class DishDeleteView(StaffRequiredMixin, DeleteView):
    model = Dish
    template_name = 'menu/dish_confirm_delete.html'
    success_url = '/menu/dishes/'