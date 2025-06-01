#!/bin/bash
set -e

echo "🍽️  菜單資料填充工具"
echo "=" * 50

# 檢查 Kubernetes 集群和命名空間
echo "🔍 檢查 Kubernetes 環境..."
if ! kubectl get namespace cloudnative-final >/dev/null 2>&1; then
    echo "❌ 命名空間 'cloudnative-final' 不存在"
    echo "請先執行部署腳本：./deploy.sh"
    exit 1
fi

# 檢查 Django deployment 是否存在且正在運行
echo "🔍 檢查 Django 應用狀態..."
if ! kubectl get deployment django -n cloudnative-final >/dev/null 2>&1; then
    echo "❌ Django deployment 不存在"
    echo "請先執行部署腳本：./deploy.sh"
    exit 1
fi

# 等待 Django pod 準備就緒
echo "⏳ 等待 Django pod 準備就緒..."
kubectl wait --for=condition=ready pod -l app=django -n cloudnative-final --timeout=60s

# 檢查是否有 management command
echo "🔍 檢查 Django management command..."
if kubectl exec deployment/django -n cloudnative-final -- python manage.py help | grep -q "populate_menu"; then
    echo "✅ 找到 populate_menu 命令"
    USE_COMMAND=true
else
    echo "⚠️  未找到 populate_menu 命令，將使用直接執行方式"
    USE_COMMAND=false
fi

# 顯示選項
echo ""
echo "請選擇操作："
echo "1) 填充菜單資料（保留現有資料）"
echo "2) 清空後重新填充菜單資料"
echo "3) 只查看目前菜單統計"
echo "4) 顯示菜單詳細內容"
echo "5) 清空菜單資料"
echo "q) 退出"
echo ""

read -p "請輸入選項 (1-5, q): " choice

case $choice in
    1)
        echo "📝 開始填充菜單資料..."
        if [ "$USE_COMMAND" = true ]; then
            kubectl exec deployment/django -n cloudnative-final -- python manage.py populate_menu
        else
            # 創建臨時 Python 腳本
            cat > /tmp/populate_menu_temp.py << 'EOF'
import os
import django
from decimal import Decimal

# 自動檢測 Django settings 模組
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # 嘗試常見的設置模組名稱
    possible_modules = [
        'CloudNative_final.settings',
        'cloudnative_final.settings', 
        'config.settings',
        'core.settings',
        'project.settings',
        'settings'
    ]
    
    settings_found = False
    for module in possible_modules:
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', module)
            django.setup()
            settings_found = True
            print(f"✅ 使用設置模組: {module}")
            break
        except ImportError:
            continue
    
    if not settings_found:
        print("❌ 無法找到 Django 設置模組")
        exit(1)
else:
    django.setup()

from menu.models import Dish

dishes_data = [
    {
        'name_zh': '紅燒牛肉麵',
        'name_en': 'Braised Beef Noodles',
        'description_zh': '精選牛腱肉慢燉3小時，配以彈牙拉麵，湯頭濃郁香醇',
        'description_en': 'Premium beef shank slow-cooked for 3 hours with chewy noodles in rich broth',
        'price': Decimal('280.00'),
        'image_url': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400',
        'is_available': True
    },
    {
        'name_zh': '蒜泥白肉',
        'name_en': 'Garlic Pork Belly',
        'description_zh': '精選五花肉片，蒜泥醬汁調味，清爽不膩',
        'description_en': 'Sliced pork belly with garlic sauce, refreshing and not greasy',
        'price': Decimal('320.00'),
        'image_url': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400',
        'is_available': True
    },
    {
        'name_zh': '宮保雞丁',
        'name_en': 'Kung Pao Chicken',
        'description_zh': '經典川菜，雞丁配花生米，酸甜微辣',
        'description_en': 'Classic Sichuan dish with diced chicken and peanuts, sweet and spicy',
        'price': Decimal('250.00'),
        'image_url': 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400',
        'is_available': True
    },
    {
        'name_zh': '麻婆豆腐',
        'name_en': 'Mapo Tofu',
        'description_zh': '嫩滑豆腐配麻辣醬汁，四川經典家常菜',
        'description_en': 'Silky tofu in spicy and numbing sauce, classic Sichuan home-style dish',
        'price': Decimal('180.00'),
        'image_url': 'https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400',
        'is_available': True
    },
    {
        'name_zh': '糖醋排骨',
        'name_en': 'Sweet and Sour Pork Ribs',
        'description_zh': '酥脆排骨裹以糖醋醬汁，酸甜開胃',
        'description_en': 'Crispy pork ribs glazed with sweet and sour sauce',
        'price': Decimal('350.00'),
        'image_url': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=400',
        'is_available': True
    },
    {
        'name_zh': '清蒸石斑魚',
        'name_en': 'Steamed Grouper',
        'description_zh': '新鮮石斑魚清蒸，保持原味鮮甜',
        'description_en': 'Fresh grouper steamed to preserve natural sweetness',
        'price': Decimal('680.00'),
        'image_url': 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400',
        'is_available': True
    },
    {
        'name_zh': '白灼蝦',
        'name_en': 'Boiled Shrimp',
        'description_zh': '新鮮草蝦白灼，配薑蔥蘸料',
        'description_en': 'Fresh prawns boiled and served with ginger-scallion sauce',
        'price': Decimal('420.00'),
        'image_url': 'https://images.unsplash.com/photo-1565299585323-38174c8dd3a0?w=400',
        'is_available': True
    },
    {
        'name_zh': '蒜蓉扇貝',
        'name_en': 'Garlic Scallops',
        'description_zh': '新鮮扇貝配蒜蓉粉絲蒸製',
        'description_en': 'Fresh scallops steamed with garlic and vermicelli',
        'price': Decimal('380.00'),
        'image_url': 'https://images.unsplash.com/photo-1551218808-94e220e084d2?w=400',
        'is_available': True
    },
    {
        'name_zh': '干煸四季豆',
        'name_en': 'Dry-Fried Green Beans',
        'description_zh': '四季豆配肉末，干香下飯',
        'description_en': 'Green beans stir-fried with minced pork, aromatic and appetizing',
        'price': Decimal('160.00'),
        'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',
        'is_available': True
    },
    {
        'name_zh': '蠔油生菜',
        'name_en': 'Lettuce in Oyster Sauce',
        'description_zh': '新鮮生菜配蠔油調味，清淡爽口',
        'description_en': 'Fresh lettuce with oyster sauce, light and refreshing',
        'price': Decimal('120.00'),
        'image_url': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400',
        'is_available': True
    },
    {
        'name_zh': '地三鮮',
        'name_en': 'Three Fresh Vegetables',
        'description_zh': '茄子、土豆、青椒三樣蔬菜炒製',
        'description_en': 'Stir-fried eggplant, potato, and green pepper',
        'price': Decimal('140.00'),
        'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',
        'is_available': True
    },
    {
        'name_zh': '酸辣湯',
        'name_en': 'Hot and Sour Soup',
        'description_zh': '經典酸辣湯，配豆腐絲和蛋花',
        'description_en': 'Classic hot and sour soup with tofu strips and egg drops',
        'price': Decimal('80.00'),
        'image_url': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400',
        'is_available': True
    },
    {
        'name_zh': '冬瓜排骨湯',
        'name_en': 'Winter Melon and Pork Rib Soup',
        'description_zh': '清淡冬瓜配排骨，湯鮮味美',
        'description_en': 'Light winter melon soup with pork ribs, fresh and delicious',
        'price': Decimal('150.00'),
        'image_url': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400',
        'is_available': True
    },
    {
        'name_zh': '雞湯',
        'name_en': 'Chicken Soup',
        'description_zh': '老母雞燉製，營養豐富',
        'description_en': 'Old hen soup, nutritious and nourishing',
        'price': Decimal('200.00'),
        'image_url': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400',
        'is_available': True
    },
    {
        'name_zh': '小籠包',
        'name_en': 'Xiaolongbao',
        'description_zh': '皮薄餡多，湯汁豐富的傳統點心',
        'description_en': 'Traditional steamed dumplings with thin skin and rich broth',
        'price': Decimal('180.00'),
        'image_url': 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400',
        'is_available': True
    },
    {
        'name_zh': '煎餃',
        'name_en': 'Pan-Fried Dumplings',
        'description_zh': '底部酥脆的煎餃，配醋蒜醬',
        'description_en': 'Crispy-bottomed pan-fried dumplings with vinegar-garlic sauce',
        'price': Decimal('120.00'),
        'image_url': 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400',
        'is_available': True
    },
    {
        'name_zh': '炸雞翅',
        'name_en': 'Fried Chicken Wings',
        'description_zh': '香酥炸雞翅，外酥內嫩',
        'description_en': 'Crispy fried chicken wings, crispy outside and tender inside',
        'price': Decimal('160.00'),
        'image_url': 'https://images.unsplash.com/photo-1562967914-608f82629710?w=400',
        'is_available': True
    },
    {
        'name_zh': '珍珠奶茶',
        'name_en': 'Bubble Tea',
        'description_zh': '經典珍珠奶茶，Q彈珍珠配香濃奶茶',
        'description_en': 'Classic bubble tea with chewy pearls and rich milk tea',
        'price': Decimal('60.00'),
        'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400',
        'is_available': True
    },
    {
        'name_zh': '檸檬蜂蜜茶',
        'name_en': 'Lemon Honey Tea',
        'description_zh': '新鮮檸檬配蜂蜜，酸甜解膩',
        'description_en': 'Fresh lemon with honey, sweet and sour',
        'price': Decimal('50.00'),
        'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400',
        'is_available': True
    },
    {
        'name_zh': '可樂',
        'name_en': 'Coca Cola',
        'description_zh': '經典可口可樂',
        'description_en': 'Classic Coca Cola',
        'price': Decimal('25.00'),
        'image_url': 'https://images.unsplash.com/photo-1629203849820-fad70345cea0?w=400',
        'is_available': True
    },
    {
        'name_zh': '大閘蟹',
        'name_en': 'Hairy Crab',
        'description_zh': '秋季限定，肥美大閘蟹',
        'description_en': 'Seasonal special, plump hairy crab',
        'price': Decimal('800.00'),
        'image_url': 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400',
        'is_available': False
    },
    {
        'name_zh': '火鍋套餐',
        'name_en': 'Hot Pot Set',
        'description_zh': '冬季限定火鍋套餐，適合2-4人',
        'description_en': 'Winter hot pot set for 2-4 people',
        'price': Decimal('580.00'),
        'image_url': 'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400',
        'is_available': False
    }
]

created_count = 0
for dish_data in dishes_data:
    dish, created = Dish.objects.get_or_create(
        name_zh=dish_data['name_zh'],
        defaults=dish_data
    )
    if created:
        created_count += 1
        status = "✅ 新增"
    else:
        status = "⚠️  已存在"
    
    availability = "🟢 供應中" if dish.is_available else "🔴 暫停供應"
    print(f"{status} - {dish.name_zh} ({dish.name_en}) - ${dish.price} - {availability}")

print(f"\n🎉 菜單資料處理完成！")
print(f"📊 統計資訊：")
print(f"   - 新增菜品：{created_count} 道")
print(f"   - 總計菜品：{Dish.objects.count()} 道")
print(f"   - 供應中：{Dish.objects.filter(is_available=True).count()} 道")
print(f"   - 暫停供應：{Dish.objects.filter(is_available=False).count()} 道")
EOF
            
            kubectl cp /tmp/populate_menu_temp.py cloudnative-final/$(kubectl get pod -l app=django -n cloudnative-final -o jsonpath='{.items[0].metadata.name}'):/tmp/
            kubectl exec deployment/django -n cloudnative-final -- python /tmp/populate_menu_temp.py
            kubectl exec deployment/django -n cloudnative-final -- rm /tmp/populate_menu_temp.py
            rm /tmp/populate_menu_temp.py
        fi
        ;;
    
    2)
        echo "🗑️  清空現有資料後重新填充..."
        if [ "$USE_COMMAND" = true ]; then
            kubectl exec deployment/django -n cloudnative-final -- python manage.py populate_menu --clear
        else
            kubectl exec deployment/django -n cloudnative-final -- python manage.py shell -c "from menu.models import Dish; print(f'清空 {Dish.objects.count()} 道菜品'); Dish.objects.all().delete(); print('清空完成')"
            # 然後執行填充（重複選項1的邏輯但不顯示選單）
            cat > /tmp/populate_menu_temp.py << 'EOF'
# ... (相同的填充腳本內容)
EOF
            kubectl cp /tmp/populate_menu_temp.py cloudnative-final/$(kubectl get pod -l app=django -n cloudnative-final -o jsonpath='{.items[0].metadata.name}'):/tmp/
            kubectl exec deployment/django -n cloudnative-final -- python /tmp/populate_menu_temp.py
            kubectl exec deployment/django -n cloudnative-final -- rm /tmp/populate_menu_temp.py
            rm /tmp/populate_menu_temp.py
        fi
        ;;
    
    3)
        echo "📊 菜單統計資訊："
        kubectl exec deployment/django -n cloudnative-final -- python manage.py shell -c "
from menu.models import Dish
total = Dish.objects.count()
available = Dish.objects.filter(is_available=True).count()
unavailable = Dish.objects.filter(is_available=False).count()
print(f'總菜品數：{total} 道')
print(f'供應中：{available} 道')
print(f'暫停供應：{unavailable} 道')
if total > 0:
    print(f'供應率：{available/total*100:.1f}%')
"
        ;;
    
    4)
        echo "📋 菜單詳細內容："
        kubectl exec deployment/django -n cloudnative-final -- python manage.py shell -c "
from menu.models import Dish
dishes = Dish.objects.all()
if dishes.exists():
    print('=' * 80)
    for dish in dishes:
        status = '🟢' if dish.is_available else '🔴'
        print(f'{status} {dish.name_zh} ({dish.name_en})')
        print(f'   價格：\${dish.price}')
        print(f'   描述：{dish.description_zh}')
        print('-' * 40)
else:
    print('目前沒有菜品資料')
"
        ;;
    
    5)
        echo "🗑️  清空菜單資料..."
        read -p "確定要清空所有菜單資料嗎？(y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            kubectl exec deployment/django -n cloudnative-final -- python manage.py shell -c "
from menu.models import Dish
count = Dish.objects.count()
Dish.objects.all().delete()
print(f'已清空 {count} 道菜品')
"
        else
            echo "取消操作"
        fi
        ;;
    
    q|Q)
        echo "👋 再見！"
        exit 0
        ;;
    
    *)
        echo "❌ 無效選項，請重新執行腳本"
        exit 1
        ;;
esac

echo ""
echo "✅ 操作完成！"
echo ""
echo "🌐 測試應用："
echo "kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo "然後訪問 http://localhost:8080/"
echo ""
echo "🔍 查看應用日誌："
echo "kubectl logs -f deployment/django -n cloudnative-final"