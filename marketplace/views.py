import uuid
from django.shortcuts import render
from django.db import transaction
from django.db.models import Sum, Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import User, DigitalProduct, Wishlist, CartItem, Order, Review, SupportTicket
from .serializers import (
    UserSerializer, ProductSerializer, WishlistSerializer,
    CartItemSerializer, OrderSerializer, ReviewSerializer, SupportTicketSerializer
)

def storefront_view(request):
    return render(request, 'marketplace/index.html')

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
                return Response({"error": f"Not enough licenses left for {product.title}."}, status=status.HTTP_400_BAD_REQUEST)
            product.stock_licenses -= item.quantity
            product.save()

            seller = product.seller
            seller.suki_wallet_balance += (product.price * item.quantity)
            seller.save()

            order = Order.objects.create(
                customer=customer,
                product=product,
                quantity=item.quantity,
                total_amount=product.price * item.quantity,
                status='PENDING',
                delivery_tracking_code=f"SUKI-DIGI-{uuid.uuid4().hex[:8].upper()}"
            )
            created_orders.append(order.id)

        customer.suki_wallet_balance -= total_cost
        customer.save()
        cart_items.delete()

        return Response({
            "message": "Checkout successful! Paid via Suki Wallet.",
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
        return Response({"message": "Order fulfilled! Canva/E-Book access link sent to customer email.", "status": order.status})

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
