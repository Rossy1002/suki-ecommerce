from rest_framework import serializers
from .models import User, DigitalProduct, ProductImage, Wishlist, CartItem, Order, Review, SupportTicket


class UserSerializer(serializers.ModelSerializer):
    effective_banner = serializers.SerializerMethodField()
    effective_logo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'phone_number', 'email', 'role',
            'suki_wallet_balance', 'saved_payment_method', 'shop_name',
            'shop_tagline', 'gender', 'country', 'region', 'city',
            'shop_logo', 'shop_banner', 'shop_banner_url',
            'effective_banner', 'effective_logo', 'shop_or_bio', 'sales_count', 'followers_count'
        ]
        read_only_fields = ['username', 'role', 'suki_wallet_balance']

    def get_effective_banner(self, obj):
        return obj.shop_banner.url if obj.shop_banner else obj.shop_banner_url

    def get_effective_logo(self, obj):
        return obj.shop_logo.url if obj.shop_logo else ''


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.username')
    customer_email = serializers.ReadOnlyField(source='customer.email')
    customer_full_name = serializers.SerializerMethodField()
    customer_location = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'customer', 'customer_name', 'customer_email',
            'customer_full_name', 'customer_location', 'product',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['customer']

    def get_customer_full_name(self, obj):
        full = f"{obj.customer.first_name} {obj.customer.last_name}".strip()
        return full if full else obj.customer.username

    def get_customer_location(self, obj):
        parts = [
            x for x in [
                getattr(obj.customer, 'city', ''),
                getattr(obj.customer, 'region', ''),
                getattr(obj.customer, 'country', '')
            ] if x
        ]
        return ", ".join(parts) if parts else "Philippines"


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')
    shop_display_name = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    sizes_list = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    download_link = serializers.CharField(required=False, allow_blank=True, default="https://www.canva.com/templates/")

    class Meta:
        model = DigitalProduct
        fields = [
            'id', 'seller', 'seller_name', 'shop_display_name', 'title', 'description',
            'whats_included', 'category', 'price', 'stock_licenses', 'available_sizes',
            'sizes_list', 'image', 'image_url', 'image_url_2', 'image_url_3',
            'gallery', 'download_link', 'is_draft', 'reviews'
        ]
        read_only_fields = ['seller']

    def get_shop_display_name(self, obj):
        return obj.seller.shop_name or obj.seller.username

    def get_gallery(self, obj):
        pics = []
        if obj.image:
            pics.append(obj.image.url)
        for extra in obj.extra_images.all().order_by('id'):
            if extra.image:
                pics.append(extra.image.url)
        if not pics:
            if obj.image_url:
                pics.append(obj.image_url)
            if obj.image_url_2:
                pics.append(obj.image_url_2)
            if obj.image_url_3:
                pics.append(obj.image_url_3)
        return pics[:10] or ["https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800&q=80"]

    def get_sizes_list(self, obj):
        if not obj.available_sizes:
            return ["Standard Digital"]
        return [s.strip() for s in obj.available_sizes.split(',') if s.strip()]


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
        fields = ['id', 'customer', 'product', 'product_title', 'product_price', 'selected_size', 'quantity']
        read_only_fields = ['customer']


class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')
    product_category = serializers.ReadOnlyField(source='product.category')
    customer_username = serializers.ReadOnlyField(source='customer.username')
    customer_full_name = serializers.SerializerMethodField()
    customer_email = serializers.ReadOnlyField(source='customer.email')
    customer_phone = serializers.ReadOnlyField(source='customer.phone_number')
    customer_address = serializers.SerializerMethodField()
    seller_shop_name = serializers.SerializerMethodField()
    seller_username = serializers.ReadOnlyField(source='product.seller.username')
    download_link = serializers.ReadOnlyField(source='product.download_link')

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_username', 'customer_full_name',
            'customer_email', 'customer_phone', 'customer_address',
            'seller_shop_name', 'seller_username', 'product', 'product_title',
            'product_category', 'selected_size', 'quantity', 'total_amount',
            'status', 'delivery_tracking_code', 'download_link', 'created_at'
        ]
        read_only_fields = ['customer', 'total_amount', 'status', 'delivery_tracking_code']

    def get_customer_full_name(self, obj):
        full = f"{obj.customer.first_name} {obj.customer.last_name}".strip()
        return full if full else obj.customer.username

    def get_customer_address(self, obj):
        parts = [
            x for x in [
                getattr(obj.customer, 'city', ''),
                getattr(obj.customer, 'region', ''),
                getattr(obj.customer, 'country', '')
            ] if x
        ]
        return ", ".join(parts) if parts else "Philippines"

    def get_seller_shop_name(self, obj):
        return obj.product.seller.shop_name or obj.product.seller.username


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ['id', 'customer', 'subject', 'message', 'resolved', 'created_at']
        read_only_fields = ['customer']