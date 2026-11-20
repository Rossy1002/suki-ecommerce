from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer / Buyer'),
        ('seller', 'Seller / Vendor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    suki_wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    saved_payment_method = models.CharField(max_length=100, default="Suki Wallet")
    shop_name = models.CharField(max_length=120, blank=True)
    shop_tagline = models.CharField(max_length=120, blank=True, default="CREATIVE DIGITAL SHOP")
    shop_banner_url = models.URLField(blank=True, default="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&q=80")
    shop_or_bio = models.TextField(blank=True, default="Verified Suki Digital Member")
    sales_count = models.PositiveIntegerField(default=0)
    followers_count = models.PositiveIntegerField(default=120)

    def __str__(self):
        return f"{self.username} ({self.role})"

class DigitalProduct(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    whats_included = models.TextField(blank=True, default="• Instant Canva Template / E-Book Access Link\n• High-Resolution Print & Digital Export Guide\n• Lifetime Commercial & Personal Use License")
    category = models.CharField(max_length=100, default="Canva Templates")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_licenses = models.PositiveIntegerField(default=50)
    available_sizes = models.CharField(max_length=200, blank=True, default="Standard Digital")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, default="https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800&q=80")
    image_url_2 = models.URLField(blank=True)
    image_url_3 = models.URLField(blank=True)
    download_link = models.URLField(default="https://www.canva.com/templates/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Wishlist(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
    selected_size = models.CharField(max_length=60, blank=True, default="Standard Digital")
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Email Delivery'),
        ('DELIVERED', 'Sent via Email'),
        ('RETURN_REQUESTED', 'Refund / Return Requested'),
        ('REFUNDED', 'Refunded to Suki Wallet'),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
    selected_size = models.CharField(max_length=60, blank=True, default="Standard Digital")
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    delivery_tracking_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SupportTicket(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
