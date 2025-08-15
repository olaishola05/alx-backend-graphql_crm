from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user = models.UUIDField(default=uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    def __str__(self):
        return self.username

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False, default='')
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'customer'
        verbose_name_plural = 'customers'
        

    def __str__(self):
        return self.name

class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stock = models.PositiveIntegerField(default=0)
    # owner = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Order(models.Model):
    order_id = models.UUIDField(default=uuid4, editable=False, unique=True)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product_ids = models.ManyToManyField(Product, related_name='orders')
    quantity = models.PositiveIntegerField()
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount= models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Order {self.order_id} by {self.customer_id.name}"
