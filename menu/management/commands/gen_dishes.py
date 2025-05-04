# menu/management/commands/gen_dishes.py
from django.core.management.base import BaseCommand
from menu.models import Dish
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Generate sample Dish entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', '-n',
            type=int,
            default=10,
            help='Number of dishes to generate (default 10)'
        )

    def handle(self, *args, **options):
        count = options['count']
        faker = Faker('zh_TW')
        created = 0
        for _ in range(count):
            Dish.objects.create(
                name_zh=faker.word() + faker.word(),
                name_en=faker.word().title(),
                description_zh=faker.sentence(nb_words=6),
                description_en=faker.sentence(nb_words=6),
                price=round(random.uniform(80, 300), 2),
                image_url=faker.image_url(),
                is_available=True
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully generated {created} dishes."))

# 使用步驟:
# 1. 安裝 Faker: pip install Faker
# 2. 確保目錄結構為 menu/management/commands/
# 3. 執行: python manage.py gen_dishes --count 20 (生成 20 筆範例資料)
