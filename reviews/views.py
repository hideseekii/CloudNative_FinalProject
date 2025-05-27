# from django.shortcuts import render

# Create your views here.
'''from django.shortcuts import render, redirect
from .forms import ReviewForm
from .models import Review
from django.contrib.auth.decorators import login_required

@login_required
def add_review(request, order_id):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            # 保存 Review 並將訂單和使用者關聯
            review = form.save(commit=False)
            review.user = request.user
            review.order_id = order_id
            review.save()
            return redirect('order_detail', order_id=order_id)
    else:
        form = ReviewForm()
    return render(request, 'reviews/add_review.html', {'form': form})'''

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ReviewForm, DishReviewForm
from .models import Review, DishReview
from orders.models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.views.generic import ListView

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        queryset = Review.objects.all()
        dish_name = self.request.GET.get('dish')
        order_id = self.request.GET.get('order_id')
        rating = self.request.GET.get('rating')
        sort = self.request.GET.get('sort')

        if dish_name:
            queryset = queryset.filter(
                order__ordercontent__dish__dish_name__icontains=dish_name
            ).distinct()

        if order_id:
            queryset = queryset.filter(order__order_id=order_id)

        if rating:
            queryset = queryset.filter(rating=rating)

        # 🔽 排序邏輯
        if sort == 'rating_desc':
            queryset = queryset.order_by('-rating')
        elif sort == 'rating_asc':
            queryset = queryset.order_by('rating')
        elif sort == 'time_asc':
            queryset = queryset.order_by('created')
        elif sort == 'time_desc':
            queryset = queryset.order_by('-created')
        else:
            queryset = queryset.order_by('-created')  # 預設最新在前

        return queryset

@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            comment = form.cleaned_data['comment']

            # ✅ 更新或建立評論，避免 UNIQUE constraint 錯誤
            review, created = Review.objects.update_or_create(
                user=request.user,
                order=order,
                defaults={
                    'rating': rating,
                    'comment': comment
                }
            )
            return redirect('orders:order_detail', order_id=order_id)
    else:
        # 如果之前填過資料，可以預填表單
        existing_review = Review.objects.filter(user=request.user, order=order).first()
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()

    return render(request, 'reviews/add_review.html', {'form': form, 'order': order})

@login_required
def add_dish_review(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
    order_items = order.items.all()  # related_name='items' 沒錯

    DishReviewFormSet = formset_factory(DishReviewForm, extra=0)

    if request.method == 'POST':
        formset = DishReviewFormSet(request.POST)

        if formset.is_valid():
            for form, item in zip(formset, order_items):
                DishReview.objects.update_or_create(
                    user=request.user,
                    order_item=item,
                    defaults={
                        'rating': form.cleaned_data['rating'],
                        'comment': form.cleaned_data['comment']
                    }
                )
            return redirect('orders:order_detail', order_id=order.order_id)

    else:
        # 建立初始資料：如果使用者已經針對某道菜品評論過，就預填
        initial_data = []
        for item in order_items:
            existing = DishReview.objects.filter(user=request.user, order_item=item).first()
            if existing:
                initial_data.append({'rating': existing.rating, 'comment': existing.comment})
            else:
                initial_data.append({})
        formset = DishReviewFormSet(initial=initial_data)

    dish_forms = zip(order_items, formset)

    return render(request, 'reviews/add_dish_review.html', {
        'order': order,
        'dish_forms': dish_forms,
        'formset': formset
    })
'''
from django.forms import modelform_factory, modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from .models import DishReview
from orders.models import Order, OrderItem
from .forms import DishReviewForm
from django.forms import formset_factory

def add_dish_review(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, consumer=request.user)
    order_items = order.items.all()  # 你可能需要確認 related_name 是否為 items

    DishReviewFormSet = formset_factory(DishReviewForm, extra=0)

    if request.method == 'POST':
        formset = DishReviewFormSet(request.POST)
        if formset.is_valid():
            for form, item in zip(formset, order_items):
                DishReview.objects.create(
                    user=request.user,
                    order=order,
                    dish=item.dish,
                    rating=form.cleaned_data['rating'],
                    comment=form.cleaned_data['comment']
                )
            return redirect('orders:order_detail', order_id=order.order_id)
    else:
        formset = DishReviewFormSet()

    dish_forms = zip(order_items, formset)

    return render(request, 'reviews/add_dish_review.html', {
        'order': order,
        'dish_forms': dish_forms,
        'formset': formset
    })'''


