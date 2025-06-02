kubectl exec deployment/django -n cloudnative-final -- python manage.py shell -c "
from decimal import Decimal
from menu.models import Dish

dishes = [
    ('紅燒牛肉麵', 'Braised Beef Noodles', 280.00, True),
    ('蒜泥白肉', 'Garlic Pork Belly', 320.00, True),
    ('宮保雞丁', 'Kung Pao Chicken', 250.00, True),
    ('麻婆豆腐', 'Mapo Tofu', 180.00, True),
    ('糖醋排骨', 'Sweet and Sour Pork Ribs', 350.00, True),
    ('清蒸石斑魚', 'Steamed Grouper', 680.00, True),
    ('白灼蝦', 'Boiled Shrimp', 420.00, True),
    ('蒜蓉扇貝', 'Garlic Scallops', 380.00, True),
    ('干煸四季豆', 'Dry-Fried Green Beans', 160.00, True),
    ('蠔油生菜', 'Lettuce in Oyster Sauce', 120.00, True),
    ('地三鮮', 'Three Fresh Vegetables', 140.00, True),
    ('酸辣湯', 'Hot and Sour Soup', 80.00, True),
    ('冬瓜排骨湯', 'Winter Melon Soup', 150.00, True),
    ('雞湯', 'Chicken Soup', 200.00, True),
    ('小籠包', 'Xiaolongbao', 180.00, True),
    ('煎餃', 'Pan-Fried Dumplings', 120.00, True),
    ('炸雞翅', 'Fried Chicken Wings', 160.00, True),
    ('珍珠奶茶', 'Bubble Tea', 60.00, True),
    ('檸檬蜂蜜茶', 'Lemon Honey Tea', 50.00, True),
    ('可樂', 'Coca Cola', 25.00, True),
    ('大閘蟹', 'Hairy Crab', 800.00, False),
    ('火鍋套餐', 'Hot Pot Set', 580.00, False),
]

created = 0
for name_zh, name_en, price, available in dishes:
    dish, is_new = Dish.objects.get_or_create(
        name_zh=name_zh,
        defaults={
            'name_en': name_en,
            'description_zh': f'{name_zh}，經典美味',
            'description_en': f'Delicious {name_en}',
            'price': Decimal(str(price)),
            'image_url': 'https://images.unsplash.com/photo-1565299585323-38174c8dd3a0?w=400',
            'is_available': available
        }
    )
    if is_new: created += 1

total = Dish.objects.count()
available_count = Dish.objects.filter(is_available=True).count()
print(f'✅ 完成！新增 {created} 道菜，總計 {total} 道，{available_count} 道供應中')
"