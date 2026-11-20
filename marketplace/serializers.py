from rest_framework import serializers
from .models import User, DigitalProduct, Wishlist, CartItem, Order, Review, SupportTicket

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'suki_wallet_balance', 'saved_payment_method', 'shop_or_bio']
        read_only_fields = ['username', 'role', 'suki_wallet_balance']

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')
    display_image = serializers.SerializerMethodField()

    class Meta:
        model = DigitalProduct
        fields = ['id', 'seller', 'seller_name', 'title', 'description', 'category', 'price', 'stock_licenses', 'image', 'image_url', 'display_image', 'download_link']
        read_only_fields = ['seller']

    def get_display_image(self, obj):
        if obj.image:
            return obj.image.url
        return obj.image_url or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&q=80"

class WishlistSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')
    class Meta:
        model = Wishlist
        fields = ['id', 'customer', 'product', 'product_title', 'added_at']
        read_only_fields = ['customer']

class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')
    product_price = serializers.ReadOnlyField(source='product.price')
    class Meta:
        model = CartItem
        fields = ['id', 'customer', 'product', 'product_title', 'product_price', 'quantity']
        read_only_fields = ['customer']

class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')
    download_link = serializers.ReadOnlyField(source='product.download_link')
    class Meta:
        model = Order
        fields = ['id', 'customer', 'product', 'product_title', 'quantity', 'total_amount', 'status', 'delivery_tracking_code', 'download_link', 'created_at']
        read_only_fields = ['customer', 'total_amount', 'status', 'delivery_tracking_code']

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.username')
    class Meta:
        model = Review
        fields = ['id', 'customer', 'customer_name', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['customer']

class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ['id', 'customer', 'subject', 'message', 'resolved', 'created_at']
        read_only_fields = ['customer']
