import graphene
from graphene_django import DjangoObjectType
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
import re

from graphene_django.filter import DjangoFilterConnectionField

from .filters import CustomerFilter, OrderFilter, ProductFilter
from .models import Customer, Product, Order


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        filterset_class = CustomerFilter
        order_by = ['name', 'email', 'created_at', 'phone']


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filterset_class = ProductFilter
        order_by = ['name', 'price', 'stock']


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filterset_class = OrderFilter
        order_by = ['total_amount', 'order_date']


def validate_phone(phone):
    if phone is None:
        return True
    pattern = re.compile(r'^(\+\d{10,15}|(\d{3}-\d{3}-\d{4}))$')
    if not pattern.match(phone):
        raise ValidationError("Invalid phone format. Expected +1234567890 or 123-456-7890.")


class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    def mutate(self, info, name, email, phone=None):
        errors = []
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format.")

        # Validate phone if provided
        try:
            validate_phone(phone)
        except ValidationError as e:
            errors.append(str(e))

        # Check if email already exists
        if Customer.objects.filter(email=email).exists():
            errors.append("Email already exists.")

        if errors:
            return CreateCustomer(customer=None, success=False, errors=errors)

        # Create customer
        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, success=True, errors=None)


class BulkCreateCustomers(graphene.Mutation):
    class CustomerInput(graphene.InputObjectType):
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        created = []
        errors = []

        with transaction.atomic():
            for idx, cust_data in enumerate(customers):
                cust_errors = []
                name = cust_data.name
                email = cust_data.email
                phone = cust_data.phone

                # Validate email
                try:
                    validate_email(email)
                except ValidationError:
                    cust_errors.append(f"Entry {idx}: Invalid email format.")

                # Validate phone
                try:
                    validate_phone(phone)
                except ValidationError as e:
                    cust_errors.append(f"Entry {idx}: {str(e)}")

                # Check duplicate email in DB
                if Customer.objects.filter(email=email).exists():
                    cust_errors.append(f"Entry {idx}: Email already exists.")

                # If errors, collect and skip creation for this entry
                if cust_errors:
                    errors.extend(cust_errors)
                    continue

                # Create customer instance but do not commit yet
                created.append(Customer(name=name, email=email, phone=phone))

            # Bulk create all valid customers at once
            if created:
                Customer.objects.bulk_create(created)

        return BulkCreateCustomers(created_customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    def mutate(self, info, name, price, stock=0):
        errors = []
        if price <= 0:
            errors.append("Price must be a positive value.")
        if stock < 0:
            errors.append("Stock cannot be negative.")

        if errors:
            return CreateProduct(product=None, success=False, errors=errors)

        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product, success=True, errors=None)


class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        errors = []

        # Validate customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            errors.append("Invalid customer ID.")

        # Validate products
        products = []
        for pid in product_ids:
            try:
                product = Product.objects.get(pk=pid)
                products.append(product)
            except Product.DoesNotExist:
                errors.append(f"Invalid product ID: {pid}")

        if not product_ids:
            errors.append("At least one product must be selected.")

        if errors:
            return CreateOrder(order=None, success=False, errors=errors)

        # Use now if order_date not provided
        order_date = order_date or timezone.now()

        # Calculate total_amount
        total_amount = sum(p.price for p in products)

        # Create order with transaction to ensure integrity
        try:
            with transaction.atomic():
                order = Order(customer=customer, order_date=order_date, total_amount=total_amount)
                order.save()
                order.products.set(products)
        except Exception as e:
            return CreateOrder(order=None, success=False, errors=[str(e)])

        return CreateOrder(order=order, success=True, errors=None)


class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(Customer)
    all_products = DjangoFilterConnectionField(Product)
    all_orders = DjangoFilterConnectionField(Order)

    def resolve_customers(self, info):
        return Customer.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
