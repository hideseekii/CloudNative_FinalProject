# orders/views.py - 修復版本
from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.views.generic import DetailView
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views.decorators.http import require_POST
from menu.models import Dish
from .models import Order, OrderItem

from django.utils.timezone import now
from django.db.models import Sum
from datetime import datetime

def staff_order_list(request):
    orders = Order.objects.filter(state=Order.State.UNFINISHED).order_by('-datetime')
    return render(request, 'orders/staff_order_list.html', {'orders': orders})

def mark_order_complete(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.state = Order.State.FINISHED
    order.save()
    return redirect('orders:staff_order_list')

def generate_monthly_report(request):
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = start.replace(year=now.year+1, month=1)
    else:
        end = start.replace(month=now.month+1)

    orders = Order.objects.filter(
        datetime__range=(start, end)
    )

    total = sum(o.total_price for o in orders)
    return render(request, 'orders/monthly_report.html', {
        'orders': orders,
        'total': total,
        'month': now.strftime('%Y年%m月')
    })


from django.core.cache import cache
from django.http import JsonResponse

from menu.models import Dish
from .models import Order, OrderItem

@method_decorator(login_required, name='dispatch')
class CheckoutView(View):
    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "購物車是空的，無法結帳。")
            return redirect('menu:cart')

        pickup_time_str = request.POST.get("pickup_time")
        try:
            if pickup_time_str == "立即取餐":
                pickup_time = timezone.now()
            else:
                today = timezone.now().date()
                pickup_time = timezone.make_aware(
                    datetime.strptime(f"{today} {pickup_time_str}", "%Y-%m-%d %H:%M")
                )
        except Exception as e:
            messages.error(request, f"取餐時間格式錯誤：{e}")
            return redirect('menu:cart')
        # 建立 Order
        order = Order.objects.create(
            consumer=request.user,
            datetime=timezone.now(),
            state=Order.State.UNFINISHED,
            total_price=0,
            pickup_time=pickup_time
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
        
        # 清除用戶的訂單歷史快取（因為新增了訂單）
        cache.delete(f'user_orders_{request.user.id}')

        messages.success(request, f"結帳成功！訂單 #{order.order_id}，總金額 NT${total}。")
        return redirect(reverse('orders:confirmation', args=[order.pk]))

@method_decorator(login_required, name='dispatch')
class OrderConfirmationView(DetailView):
    model = Order
    template_name = 'orders/confirmation.html'
    context_object_name = 'order'

# === 修復後的訂單詳情 ===
@login_required
def order_detail(request, order_id):
    """修復版本：更安全的快取實作"""
    try:
        # 先從資料庫獲取訂單（確保用戶有權限查看）
        order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
        
        # 嘗試從快取獲取訂單項目
        cache_key = f'order_items_{order_id}'
        cached_items = cache.get(cache_key)
        
        if cached_items is None:
            print(f"🔴 Cache MISS: 訂單項目 {order_id}")
            # 獲取訂單項目
            order_items = order.items.select_related('dish').all()
            
            # 序列化為可快取的格式
            items_data = []
            for item in order_items:
                items_data.append({
                    'id': item.pk,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'dish_name_zh': item.dish.name_zh,
                    'dish_name_en': item.dish.name_en,
                    'dish_image_url': item.dish.image_url,
                    'subtotal': float(item.quantity * item.unit_price)
                })
            
            # 快取 2 分鐘
            cache.set(cache_key, items_data, 120)
            
            context = {
                'order': order,
                'order_items': order_items,  # 使用原始 QuerySet
            }
        else:
            print(f"🟢 Cache HIT: 訂單項目 {order_id}")
            # 從快取重建顯示資料
            context = {
                'order': order,
                'order_items': cached_items,  # 使用快取的資料
                'use_cached_items': True,  # 標記使用快取資料
            }
        
        return render(request, 'orders/order_detail.html', context)
        
    except Exception as e:
        # 如果出錯，記錄錯誤並回到訂單歷史
        print(f"❌ 訂單詳情錯誤: {e}")
        messages.error(request, "載入訂單詳情時發生錯誤")
        return redirect('orders:order_history')

# === 修復後的訂單歷史 ===
@login_required
def order_history(request):
    """修復版本：更簡單的快取實作"""
    try:
        cache_key = f'user_orders_{request.user.id}'
        cached_orders = cache.get(cache_key)
        
        if cached_orders is None:
            print(f"🔴 Cache MISS: 用戶 {request.user.id} 的訂單歷史")
            # 直接使用 QuerySet，不要過度序列化
            orders = Order.objects.filter(consumer=request.user).order_by('-datetime')
            
            # 簡單快取：只快取訂單 ID 列表
            order_ids = list(orders.values_list('order_id', flat=True))
            cache.set(cache_key, order_ids, 300)  # 快取 5 分鐘
            
            context = {'orders': orders}
        else:
            print(f"🟢 Cache HIT: 用戶 {request.user.id} 的訂單歷史")
            # 根據快取的 ID 重新查詢（保持 Django ORM 的完整性）
            orders = Order.objects.filter(
                order_id__in=cached_orders, 
                consumer=request.user
            ).order_by('-datetime')
            context = {'orders': orders}
        
        return render(request, 'orders/order_history.html', context)
        
    except Exception as e:
        print(f"❌ 訂單歷史錯誤: {e}")
        # 發生錯誤時，直接查詢資料庫
        orders = Order.objects.filter(consumer=request.user).order_by('-datetime')
        return render(request, 'orders/order_history.html', {'orders': orders})

# === 簡化版 API 端點 ===
@login_required
def order_status_api(request, order_id):
    """簡化版本：基本的訂單狀態查詢"""
    try:
        order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
        
        data = {
            'order_id': order.order_id,
            'state': order.state,
            'state_display': order.get_state_display(),
            'datetime': order.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'total_price': float(order.total_price),
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# === 快取管理工具函數 ===
def clear_order_cache(order_id, user_id):
    """清除特定訂單的相關快取"""
    cache.delete(f'order_items_{order_id}')
    cache.delete(f'user_orders_{user_id}')
    print(f"🧹 已清除訂單 {order_id} 相關快取")

def clear_user_order_cache(user_id):
    """清除特定用戶的所有訂單快取"""
    cache.delete(f'user_orders_{user_id}')
    print(f"🧹 已清除用戶 {user_id} 的訂單快取")
