import django_filters
from crm.models import Customer, Order, Product
import re


class CustomerFilter(django_filters.FilterSet):
  
    phone_pattern = django_filters.CharFilter(
        field_name='phone',
        lookup_expr='regex',
        label="Phone Number Pattern (regex, e.g., ^\\+1.*)"
    )
  
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'created_at': ['date__gte', 'date__lte'],
        }


class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte', 'lt'],
            'created_at': ['exact', 'day__gte', 'day__lte'],
        }
        
class OrderFilter(django_filters.FilterSet):
    customer_name = django_filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        label="Customer Name (contains)"
    )
    
    product_name = django_filters.CharFilter(
        field_name='product__name',
        lookup_expr='icontains',
        label="Product Name (contains)"
    )
    
    product_id = django_filters.UUIDFilter(
        field_name='product__product_id',
        lookup_expr='exact',
        label="Product ID (exact)"
    )

    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte'],
            'order_date': ['exact', 'day__gte', 'day__lte', 'date__range'],
        }