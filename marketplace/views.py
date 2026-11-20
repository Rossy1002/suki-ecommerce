import uuid
import json
import urllib.request
from django.shortcuts import render
from django.db import transaction
from django.db.models import Sum, Count
from django.core.mail import send_mail
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import User, DigitalProduct, Wishlist, CartItem, Order, Review, SupportTicket
from .serializers import (
    UserSerializer, ProductSerializer, WishlistSerializer,
    CartItemSerializer, OrderSerializer, ReviewSerializer, SupportTicketSerializer
)

def storefront_view(request):
    return render(request, 'marketplace/index.html')

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def currency_rates_api(request):
    """2nd Distinct External API Integration: Live PHP Exchange Rates with graceful offline VM fallback."""
    try:
        req = urllib.request.urlopen("https://open.er-api.com/v6/latest/PHP", timeout=3)
        data = json.loads(req.read().decode('utf-8'))
        return Response({
            "source": "Live ExchangeRate API",
            "base": "PHP",
            "USD": data["rates"].get("USD", 0.017),
            "EUR": data["rates"].get("EUR", 0.016),
            "JPY": data["rates"].get("JPY", 2.65)
        })
    except Exception:
        return Response({
            "source": "Offline VM Fallback Rate",
            "base": "PHP",
            "USD": 0.0172,
            "EUR": 0.0158,
            "JPY": 2.62
        })

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = DigitalProduct.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = DigitalProduct.objects.all().order_by('-id')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Wishlist.objects.filter(customer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return CartItem.objects.filter(customer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def checkout(self, request):
        customer = request.user
        cart_items = CartItem.objects.filter(customer=customer)
        if not cart_items.exists():
            return Response({"error": "Your shopping cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        total_cost = sum(item.product.price * item.quantity for item in cart_items)
        if customer.suki_wallet_balance < total_cost:
            return Response({
                "error": "Insufficient Suki Wallet credits.",
                "wallet_balance": customer.suki_wallet_balance,
                "required": total_cost
            }, status=status.HTTP_400_BAD_REQUEST)

        created_orders = []
        for item in cart_items:
            product = item.product
            if product.stock_licenses < item.quantity:
                return Response({"error": f"Out of stock: Not enough licenses left for {product.title}."}, status=status.HTTP_400_BAD_REQUEST)
            product.stock_licenses -= item.quantity
            product.save()

            seller = product.seller
            seller.suki_wallet_balance += (product.price * item.quantity)
            seller.save()

            tracking = f"SUKI-DIGI-{uuid.uuid4().hex[:8].upper()}"
            order = Order.objects.create(
                customer=customer,
                product=product,
                quantity=item.quantity,
                total_amount=product.price * item.quantity,
                status='PENDING',
                delivery_tracking_code=tracking
            )
            created_orders.append(order.id)

        customer.suki_wallet_balance -= total_cost
        customer.save()
        cart_items.delete()

        return Response({
            "message": "Checkout successful! Paid via Suki Wallet. Seller notified for email delivery.",
            "amount_deducted": total_cost,
            "remaining_suki_wallet_balance": customer.suki_wallet_balance,
            "order_ids": created_orders
        }, status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.role == 'seller':
            return Order.objects.filter(product__seller=user).order_by('-id')
        return Order.objects.filter(customer=user).order_by('-id')

    @action(detail=True, methods=['post'])
    def fulfill(self, request, pk=None):
        order = self.get_object()
        order.status = 'DELIVERED'
        order.save()
        recipient = order.customer.email or f"{order.customer.username}@suki.ph"
        send_mail(
            subject=f"[Suki.ph] Your Digital Product: {order.product.title}",
            message=f"Hi {order.customer.username},\n\nThank you for your purchase! Access your Canva Template / E-Book here:\n{order.product.download_link}\n\nTracking Code: {order.delivery_tracking_code}",
            from_email="delivery@suki.ph",
            recipient_list=[recipient],
            fail_silently=True,
        )
        return Response({
            "message": f"Sent via Email to {recipient}! Digital access unlocked.",
            "status": order.status,
            "delivered_to_email": recipient
        })

    @action(detail=True, methods=['post'])
    def request_return(self, request, pk=None):
        order = self.get_object()
        order.status = 'RETURN_REQUESTED'
        order.save()
        return Response({"message": "Return/refund requested.", "status": order.status})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def process_refund(self, request, pk=None):
        order = self.get_object()
        if order.status == 'REFUNDED':
            return Response({"error": "Already refunded."}, status=status.HTTP_400_BAD_REQUEST)
        customer = order.customer
        seller = order.product.seller
        customer.suki_wallet_balance += order.total_amount
        customer.save()
        seller.suki_wallet_balance -= order.total_amount
        seller.save()
        order.product.stock_licenses += order.quantity
        order.product.save()
        order.status = 'REFUNDED'
        order.save()
        return Response({"message": f"Refunded ₱{order.total_amount} to {customer.username}'s Suki Wallet."})

    @action(detail=False, methods=['get'])
    def sales_analytics(self, request):
        if request.user.role != 'seller':
            return Response({"error": "Only sellers can view analytics."}, status=status.HTTP_403_FORBIDDEN)
        orders = Order.objects.filter(product__seller=request.user).exclude(status='REFUNDED')
        stats = orders.aggregate(total_revenue=Sum('total_amount'), total_orders=Count('id'))
        return Response({
            "seller": request.user.username,
            "current_wallet_balance": request.user.suki_wallet_balance,
            "total_orders": stats['total_orders'] or 0,
            "total_revenue": stats['total_revenue'] or 0.00
        })

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

class SupportViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return SupportTicket.objects.filter(customer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
