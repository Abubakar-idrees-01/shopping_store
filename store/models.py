from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.db.models import Avg,Sum
import uuid
from django.contrib import admin


# -----------------------------
# Category
# -----------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# -----------------------------
# Product
# -----------------------------
class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ("stitched", "Stitched"),
        ("unstitched", "Unstitched"),
    ]

    PIECE_TYPE_CHOICES = [
        ("2-piece", "2 Piece"),
        ("3-piece", "3 Piece"),
    ]

    # Identification
    name = models.CharField(max_length=200)
    product_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        
        blank=True,
        help_text="Auto-generated unique SKU"
    )
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    # Core Details
    description = models.TextField(blank=True)
    about_product = models.TextField(blank=True, help_text="Detailed description for 'About the Product'")
    disclaimer = models.TextField(blank=True, help_text="Disclaimer for product")

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Classification
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default="unstitched")
    piece_type = models.CharField(max_length=20, choices=PIECE_TYPE_CHOICES, default="3-piece")
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, blank=True)

    # Attributes
    fabric = models.CharField(max_length=100, blank=True, help_text="e.g. Lawn, Cotton, Silk")
    color = models.CharField(max_length=100, blank=True)
    sizes = models.CharField(max_length=100, blank=True, help_text="Comma-separated sizes e.g. S,M,L,XL")

    # Inventory
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Media
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    # Delivery Info
    delivery_nationwide = models.CharField(max_length=100, default="2-3 working days nationwide")
    delivery_international = models.CharField(max_length=100, default="International Dileveries are not currently avaiable")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.product_code})"

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name)

        # Auto-generate unique product_code
        if not self.product_code:
            prefix = f"{self.product_type[:3].upper()}-{self.piece_type[0]}P"
            unique_id = uuid.uuid4().hex[:5].upper()
            self.product_code = f"{prefix}-{unique_id}"

        super().save(*args, **kwargs)

    # === Pricing Helpers ===
    @property
    def final_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def discount_percentage(self):
        if self.discount_price and self.discount_price < self.price:
            return int(100 - (self.discount_price / self.price * 100))
        return 0

    # === Extra Helpers ===
    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    @property
    def is_low_stock(self):
        return self.stock < 5


# -----------------------------
# Wishlist
# -----------------------------
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wishlist")
    products = models.ManyToManyField(Product, blank=True, related_name="wishlisted_by")

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


# -----------------------------
# Order
# -----------------------------
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("COD", "Cash on Delivery"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # ✅ New fields with default null/blank
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    province = models.CharField(max_length=50, blank=True, null=True)

    shipping_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_METHOD_CHOICES, default="COD"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending"
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def calculate_total(self):
        return sum(item.get_total() for item in self.items.all())

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not is_new:
            old_order = Order.objects.get(pk=self.pk)
            old_status = old_order.status

            if old_status != "Cancelled" and self.status == "Cancelled":
                for item in self.items.all():
                    if item.product:
                        item.product.stock += item.quantity
                        item.product.save()

        super().save(*args, **kwargs)

        self.total_amount = self.calculate_total()
        super().save(update_fields=["total_amount"])

        total_revenue = Order.objects.filter(status="Delivered").aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        print("Total Revenue from Delivered Orders:", total_revenue)



# -----------------------------
# Order Item
# -----------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Snapshot of product price at checkout"
    )
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        # ✅ Take snapshot of product price at checkout
        if self.product and not self.price:
            self.price = self.product.final_price  
        super().save(*args, **kwargs)

    def get_total(self):
        """Return total price for this order item."""
        return (self.price or 0) * self.quantity

    def __str__(self):
        product_name = self.product.name if self.product else "Deleted product"
        return f"{self.quantity} × {product_name} (Order #{self.order.id})"


# -----------------------------
# Review
# -----------------------------
class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating} Stars"


# -----------------------------
# Cart Item (Session Based)
# -----------------------------
class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def price(self):
        return self.product.discount_price or self.product.price

    @property
    def subtotal(self):
        return self.price * self.quantity


