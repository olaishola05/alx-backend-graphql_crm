import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model, authenticate
from .models import Customer, Product, Order, User
import graphql_jwt
from graphql_jwt.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re
from graphene.types import JSONString
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from django.db import transaction, IntegrityError
from decimal import Decimal

User = get_user_model()

def validate_password_strength(password):
    """Custom password strength validation"""
    errors = []
    
    if len(password) < 8:
        errors.append("Must be at least 8 characters long")
    
    if len(password) > 128:
        errors.append("Must be less than 128 characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Must contain at least one lowercase letter")
    
    if not re.search(r"[0-9]", password):
        errors.append("Must contain at least one number")
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("Must contain at least one special character")
    
    # Check for common passwords
    common_passwords = ['password', '123456', 'qwerty', 'abc123']
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return errors  
class UserType(DjangoObjectType):
  class Meta:
    model = User
    fields = ("id", 'user','email', 'username', 'first_name', 'last_name', 'is_staff')
    
class CustomerType(DjangoObjectType):
  class Meta:
    model = Customer
    fields = "__all__"
    filter_fields = ['name', 'email', 'phone']
    interfaces = (graphene.relay.Node,)
    
class ProductType(DjangoObjectType):
  class Meta:
    model = Product
    fields = "__all__"
    filter_fields = ['name', 'price', 'stock']
    interfaces = (graphene.relay.Node,)
    
    
class OrderType(DjangoObjectType):
  class Meta:
    model = Order
    fields = "__all__"
    filter_fields = ['order_date', 'total_amount']
    interfaces = (graphene.relay.Node,)
     
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    users = graphene.List(UserType)
    customer = graphene.relay.Node.Field(CustomerType)
    all_customers = DjangoFilterConnectionField(CustomerType)
    
    product = graphene.relay.Node.Field(ProductType)
    all_products = DjangoFilterConnectionField(ProductType)

    order = graphene.relay.Node.Field(OrderType)
    all_orders = DjangoFilterConnectionField(OrderType)
    
    # @login_required
    # def resolve_users(self, info):
      # user = info.context.user
      # print("Logged user:", user.is_authenticated)
      # if user.is_authenticated:
        # return User.objects.all()
    # 
    # def resolve_customers(self, info):
      # return Customer.objects.all()
    # 
    # def resolve_customer_by_id(self, info, id):
      # try:
        # return Customer.objects.get(id=id)
      # except Customer.DoesNotExist:
        # return None
    # def resolve_products(self, info):
      # return Product.objects.all()
    # 
    # def resolve_product_by_id(self, info, id):
      # try:
        # return Product.objects.get(product_id=id)
      # except Product.DoesNotExist:
        # return 'Product deos not exist'
    # 
    # def resolve_orders(self, info):
      # return Order.objects.all()
    # 
    # def resolve_order_by_id(self, info, id):
      # try:
        # return Order.objects.get(order_id=id)
      # except Order.DoesNotExist:
        # return 'Order does not exist or not found'
      # 
      # 
    # def resolve_order_by_customer(self, info, customer_id):
      # try:
        # return Order.objects.all().filter(customer_id=customer_id)
      # except Customer.DoesNotExist:
        # return f"Customer with {customer_id} does not exist or found!"

class ErrorType(graphene.ObjectType):
    field = graphene.String()
    message = graphene.String()
class LoginMutation(graphene.Mutation):
  class Arguments:
    email = graphene.String(required=True)
    password = graphene.String(required=True)
  
  token = graphene.String()
  user = graphene.Field(UserType)
  success = graphene.Boolean()
  errors = graphene.List(graphene.String)
  
  def mutate(self, info, email, password):
    user = authenticate(email=email, password=password)
    if user:
      token = graphql_jwt.shortcuts.get_token(user)   # type: ignore
      return LoginMutation(
        token=token, # pyright: ignore[reportCallIssue]
        user=user, # pyright: ignore[reportCallIssue]
        success=True, # pyright: ignore[reportCallIssue]e,
        errors=[] # pyright: ignore[reportCallIssue]
      )
      
    return LoginMutation(
      success=False,
      errors=["Invalid credential"]
    )
    
# Advanced registration with custom validation
class RegisterMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_confirm = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        phone = graphene.String()
        terms_accepted = graphene.Boolean(required=True)
    
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = JSONString()
    token = graphene.String()
    
    def mutate(self, info, username, email, password, password_confirm, 
               terms_accepted, first_name=None, last_name=None, phone=None):
        
        errors = {
            'username': [],
            'email': [],
            'password': [],
            'general': []
        }
        
        if not terms_accepted:
            errors['general'].append("You must accept the terms and conditions")
        
        username = username.strip()
        if len(username) < 3:
            errors['username'].append("Must be at least 3 characters long")
        elif len(username) > 30:
            errors['username'].append("Must be less than 30 characters long")
        elif not re.match("^[a-zA-Z0-9_]+$", username):
            errors['username'].append("Can only contain letters, numbers, and underscores")
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'].append("Username already taken")
        
        email = email.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            errors['email'].append("Invalid email format")
        
        if User.objects.filter(email__iexact=email).exists():
            errors['email'].append("Email already registered")
        
        if password != password_confirm:
            errors['password'].append("Passwords do not match")
        
        password_errors = validate_password_strength(password)
        errors['password'].extend(password_errors)
        
        if phone:
            phone = phone.strip()
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                errors['general'].append("Invalid phone number format")
        
        has_errors = any(error_list for error_list in errors.values())
        
        if has_errors:
            return RegisterMutation(
                success=False,
                errors=errors,
                user=None,
                token=None
            )
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            # Customer.objects.create(
                # user=user,
                # phone=phone or '',
                # email=email
            # )
            # 
            return RegisterMutation(
                user=user, # type: ignore
                success=True, # type: ignore
                errors={}, # type: ignore
            )
            
        except Exception as e:
            return RegisterMutation(
                success=False,
                errors={'general': [f"Registration failed: {str(e)}"]},
                user=None,
            )

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    # Output = graphene.relay.ClientIDMutation.Output # type: ignore
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, name, email, phone=None):
        errors = []
        try:
            validate_email(email)
        except ValidationError:
            errors.append(ErrorType(field="email", message="Invalid email format."))

        if Customer.objects.filter(email=email).exists():
            errors.append(ErrorType(field="email", message="Email already exists."))
        if phone:
            if not re.fullmatch(r"^\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$", phone):
                errors.append(ErrorType(field="phone", message="Invalid phone format. Use formats like +1234567890 or 123-456-7890."))

        if errors:
            return CreateCustomer(success=False, message="Validation failed.", errors=errors)

        try:
            customer = Customer.objects.create(name=name, email=email, phone=phone)
            return CreateCustomer(customer=customer, success=True, message="Customer created successfully.")
        except IntegrityError:
            errors.append(ErrorType(field="email", message="Email already exists (database constraint)."))
            return CreateCustomer(success=False, message="Customer creation failed.", errors=errors)
        except Exception as e:
            errors.append(ErrorType(field="__all__", message=f"An unexpected error occurred: {str(e)}"))
            return CreateCustomer(success=False, message="Customer creation failed.", errors=errors)


class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class BulkCreateCustomerErrorType(graphene.ObjectType):
    record_index = graphene.Int()
    field = graphene.String()
    message = graphene.String()
    
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers_data = graphene.List(CustomerInput, required=True)

    successful_customers = graphene.List(CustomerType)
    errors = graphene.List(BulkCreateCustomerErrorType)
    message = graphene.String()

    def mutate(self, info, customers_data):
        created_customers = []
        failed_records_errors = []

        for i, customer_input in enumerate(customers_data):
            record_errors = []
            name = customer_input.name
            email = customer_input.email
            phone = customer_input.phone
            
            try:
                validate_email(email)
            except ValidationError:
                record_errors.append(ErrorType(field="email", message="Invalid email format."))

            if Customer.objects.filter(email=email).exists():
                record_errors.append(ErrorType(field="email", message="Email already exists."))

            if phone:
                if not re.fullmatch(r"^\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$", phone):
                    record_errors.append(ErrorType(field="phone", message="Invalid phone format. Use formats like +1234567890 or 123-456-7890."))

            if record_errors:
                for error in record_errors:
                    failed_records_errors.append({
                        'record_index': i,
                        'field': error.field,
                        'message': error.message
                    })
                continue

            try:
                with transaction.atomic():
                    customer = Customer.objects.create(
                        name=name,
                        email=email,
                        phone=phone
                    )
                    created_customers.append(customer)
            except IntegrityError:
                failed_records_errors.append({
                    'record_index': i,
                    'field': "email",
                    'message': "Email already exists (database constraint)."
                })
            except Exception as e:
                failed_records_errors.append({
                    'record_index': i,
                    'field': "__all__",
                    'message': f"An unexpected error occurred: {str(e)}"
                })

        message = "Bulk customer creation completed."
        if failed_records_errors:
            message += f" Some records failed ({len(failed_records_errors)} errors)."
        else:
            message += " All customers created successfully."

        formatted_errors = [BulkCreateCustomerErrorType(**err) for err in failed_records_errors]


        return BulkCreateCustomers(
            successful_customers=created_customers,
            errors=formatted_errors,
            message=message
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int(default_value=0)

    # Output = graphene.relay.ClientIDMutation.Output
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, name, price, stock=0):
        errors = []

        if price <= 0:
            errors.append(ErrorType(field="price", message="Price must be positive."))
        if stock < 0:
            errors.append(ErrorType(field="stock", message="Stock cannot be negative."))

        if errors:
            return CreateProduct(success=False, message="Validation failed.", errors=errors)

        try:
            product = Product.objects.create(name=name, price=price, stock=stock)
            return CreateProduct(product=product, success=True, message="Product created successfully.")
        except Exception as e:
            errors.append(ErrorType(field="__all__", message=f"An unexpected error occurred: {str(e)}"))
            return CreateProduct(success=False, message="Product creation failed.", errors=errors)
          
          

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    # Output = graphene.relay.ClientIDMutation.Output
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        errors = []
        
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            errors.append(ErrorType(field="customer_id", message="Invalid customer ID."))

        if not product_ids:
            errors.append(ErrorType(field="product_ids", message="At least one product must be selected."))
        
        products = []
        total_amount = Decimal('0.00')
        if product_ids:
            fetched_products = Product.objects.filter(id__in=product_ids)
            if fetched_products.count() != len(product_ids):
                # This means some product IDs were not found
                found_ids = {str(p.id) for p in fetched_products}
                invalid_ids = [pid for pid in product_ids if pid not in found_ids]
                for inv_id in invalid_ids:
                    errors.append(ErrorType(field="product_ids", message=f"Product with ID '{inv_id}' not found."))
            
            products = list(fetched_products)
            total_amount = sum(p.price for p in products)


        if errors:
            return CreateOrder(success=False, message="Validation failed.", errors=errors)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer_id=customer,
                    order_date=order_date if order_date else graphene.DateTime.now()
                )
                order.product_ids.set(products)
                order.total_amount = total_amount
                order.save()

            return CreateOrder(order=order, success=True, message="Order created successfully.")
        except Exception as e:
            errors.append(ErrorType(field="__all__", message=f"An unexpected error occurred: {str(e)}"))
            return CreateOrder(success=False, message="Order creation failed.", errors=errors)

class Mutation(graphene.ObjectType):
    
  login = LoginMutation.Field()
  register = RegisterMutation.Field()
  create_customer = CreateCustomer.Field()
  token = graphql_jwt.ObtainJSONWebToken.Field()
  verify_token = graphql_jwt.Verify.Field()
  refresh_token = graphql_jwt.Refresh.Field()
  delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
