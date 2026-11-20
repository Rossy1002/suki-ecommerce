import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suki_core.settings')
django.setup()

from marketplace.models import User, DigitalProduct

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@suki.ph', 'admin1234', role='seller')

c1, _ = User.objects.get_or_create(username='customer1', defaults={'email': 'juan@suki.ph', 'role': 'customer', 'suki_wallet_balance': 5000.00})
c1.set_password('pass1234')
c1.save()

c2, _ = User.objects.get_or_create(username='customer2', defaults={'email': 'maria@suki.ph', 'role': 'customer', 'suki_wallet_balance': 5000.00})
c2.set_password('pass1234')
c2.save()

s1, _ = User.objects.get_or_create(username='seller1', defaults={'email': 'studio@suki.ph', 'role': 'seller', 'suki_wallet_balance': 0.00})
s1.set_password('sell1234')
s1.save()

s2, _ = User.objects.get_or_create(username='seller2', defaults={'email': 'templates@suki.ph', 'role': 'seller', 'suki_wallet_balance': 0.00})
s2.set_password('sell1234')
s2.save()

DigitalProduct.objects.get_or_create(
    title="All-in-One Notion Student & Freelancer Tracker",
    seller=s1,
    defaults={'description': 'Customizable Notion template.', 'category': 'Notion Templates', 'price': 350.00, 'stock_licenses': 100}
)
DigitalProduct.objects.get_or_create(
    title="Procreate Filipino Brush Pack (50 Brushes)",
    seller=s2,
    defaults={'description': 'Digital illustration brushes.', 'category': 'Digital Art', 'price': 499.00, 'stock_licenses': 50}
)
print("Seed data successfully created!")
