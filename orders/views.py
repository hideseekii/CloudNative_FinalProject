# orders/views.py

from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.views.generic import DetailView
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from menu.models import Dish
from .models import Order, OrderItem


@method_decorator(login_required, name='dispatch')
class CheckoutView(View):
    """
    處理 POST /orders/checkout/：
    1. 從 session 取 cart，建立 Order + OrderItem
    2. 計算總價，存入 order.total_price
    3. 清空 session cart，redirect 到 confirmation
    """
    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "購物車是空的，無法結帳。")
            return redirect('menu:cart')

        # 建立 Order
        order = Order.objects.create(
            consumer=request.user,
            datetime=timezone.now(),
            state=Order.State.UNFINISHED,
            total_price=0
        )

        total = 0
        # 建立每筆 OrderItem
        for dish_id, qty in cart.items():
            dish = get_object_or_404(Dish, pk=dish_id)
            subtotal = dish.price * qty
            total += subtotal

            OrderItem.objects.create(
                order=order,
                dish=dish,
                quantity=qty,
                unit_price=dish.price
            )

        # 更新並儲存總價
        order.total_price = total
        order.save()

        # 清空購物車
        request.session['cart'] = {}
        request.session.modified = True

        messages.success(request, f"結帳成功！訂單 #{order.order_id}，總金額 NT${total}。")
        return redirect(reverse('orders:confirmation', args=[order.pk]))


@method_decorator(login_required, name='dispatch')
class OrderConfirmationView(DetailView):
    """
    顯示剛剛建立的 Order 明細
    URL: /orders/confirmation/<pk>/
    """
    model = Order
    template_name = 'orders/confirmation.html'
    context_object_name = 'order'


# 以下保留你原本的 function-based views

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'order_items': order.items.all(),
    })


@login_required
def order_history(request):
    orders = Order.objects.filter(consumer=request.user).order_by('-datetime')
    return render(request, 'orders/order_history.html', {'orders': orders})
