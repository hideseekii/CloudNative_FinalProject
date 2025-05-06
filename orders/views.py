# orders/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def order_detail(request, order_id):
    # Ensure user can only view their own orders
    order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.all()
    }
    
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(consumer=request.user).order_by('-datetime')
    
    context = {
        'orders': orders
    }
    
    return render(request, 'orders/order_history.html', context)