import os
import django
import random
from datetime import datetime
from django.utils.timezone import now

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order

def seed_customers():
    customers = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol White", "email": "carol@example.com", "phone": None},
    ]
    for data in customers:
        Customer.objects.get_or_create(**data)
    print(f"Seeded {len(customers)} customers.")

def seed_products():
    products = [
        {"name": "Laptop", "price": 1200.00, "stock": 5},
        {"name": "Smartphone", "price": 800.00, "stock": 10},
        {"name": "Headphones", "price": 150.00, "stock": 25},
    ]
    for data in products:
        Product.objects.get_or_create(**data)
    print(f"Seeded {len(products)} products.")

def seed_orders():
    customers = list(Customer.objects.all())
    products = list(Product.objects.all())

    if not customers or not products:
        print("Add customers and products first.")
        return

    for i in range(3):
        customer = random.choice(customers)
        selected_products = random.sample(products, k=2)
        total_amount = sum(p.price for p in selected_products)

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=now()
        )
        order.products.set(selected_products)
    print("Seeded 3 orders.")

if __name__ == "__main__":
    seed_customers()
    seed_products()
    seed_orders()
    print("✅ Database seeded successfully.")
