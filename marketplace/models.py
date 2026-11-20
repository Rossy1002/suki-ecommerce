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
    shop_or_bio = models.TextField(blank=True, default="Verified Suki Digital Member")

    def __str__(self):
        return f"{self.username} ({self.role}) - Credits: ₱{self.suki_wallet_balance}"

class DigitalProduct(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, default="Templates & E-Books")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_licenses = models.PositiveIntegerField(default=50)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url = models.URLField(blank=True, default="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&q=80")
    download_link = models.URLField(default="https://suki.ph/downloads/sample-asset.zip")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (₱{self.price} | Stock: {self.stock_licenses})"

class Wishlist(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Fulfillment'),
        ('DELIVERED', 'Sent via Email'),
        ('RETURN_REQUESTED', 'Refund / Return Requested'),
        ('REFUNDED', 'Refunded to Suki Wallet'),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(DigitalProduct, on_delete=models.CASCADE)
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
