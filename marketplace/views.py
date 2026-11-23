import uuid
import json
import urllib.request
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import Sum, Count
from django.core.mail import send_mail
from django.core.files.base import ContentFile
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import User, DigitalProduct, ProductImage, Wishlist, CartItem, Order, Review, SupportTicket
from .serializers import (
    UserSerializer, ProductSerializer, WishlistSerializer,
    CartItemSerializer, OrderSerializer, ReviewSerializer, SupportTicketSerializer
)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_login_view(request):
    login_id = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not login_id and not password:
        return Response({'error': 'Please enter your email or username and password.'}, status=status.HTTP_400_BAD_REQUEST)
    if not login_id:
        return Response({'error': 'Please enter your email or username.'}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({'error': 'Please enter your password.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=login_id, password=password)
    if user is None:
        matched = User.objects.filter(email__iexact=login_id).first() or User.objects.filter(username__iexact=login_id).first()
        if matched:
            user = authenticate(request, username=matched.username, password=password)
    if user is not None:
        login(request, user)
        return Response({'message': 'Logged in successfully!', 'role': user.role})
    return Response({'error': 'Incorrect email/username or password. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_register_view(request):
    role = request.data.get('role', 'seller')
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    shop_name = request.data.get('shop_name', '').strip()
    gender = request.data.get('gender', '').strip()
    phone_number = request.data.get('phone_number', '').strip()
    country = request.data.get('country', 'Philippines').strip()
    region = request.data.get('region', '').strip()
    city = request.data.get('city', '').strip()
    raw_user = request.data.get('username', '').strip()

    if not email or not password:
        return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email__iexact=email).exists():
        return Response({'error': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    if role == 'seller':
        if not shop_name or not first_name or not last_name:
            return Response({'error': 'Shop Name, First Name, and Last Name are required.'}, status=status.HTTP_400_BAD_REQUEST)
        base_handle = ''.join(c for c in shop_name.lower() if c.isalnum())[:16] or email.split('@')[0]
    else:
        base_handle = raw_user or email.split('@')[0]

    username = base_handle
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_handle}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        role=role,
        suki_wallet_balance=0.00 if role == 'seller' else 5000.00,
        shop_name=shop_name if role == 'seller' else '',
        shop_tagline='CREATIVE DIGITAL SHOP' if role == 'seller' else '',
        gender=gender,
        phone_number=phone_number,
        country=country,
        region=region,
        city=city,
        shop_or_bio=''
    )
    if 'shop_logo' in request.FILES:
        user.shop_logo = request.FILES['shop_logo']
    if 'shop_banner' in request.FILES:
        user.shop_banner = request.FILES['shop_banner']
    user.save()

    login(request, user)
    return Response({'message': 'Shop created!', 'role': user.role, 'username': user.username}, status=status.HTTP_201_CREATED)


def storefront_view(request):
    return render(request, 'marketplace/index.html')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_shops_api(request):
    """Public endpoint so guests can view Featured Seller Shops without logging in."""
    sellers = User.objects.filter(role='seller', is_superuser=False).order_by('id')
    result = []
    for s in sellers:
        prods = DigitalProduct.objects.filter(seller=s).order_by('-id')
        result.append({
            "id": s.id,
            "username": s.username,
            "shop_name": s.shop_name or s.username,
            "shop_tagline": s.shop_tagline or "DIGITAL CREATOR SHOP",
            "shop_banner_url": s.shop_banner.url if s.shop_banner else s.shop_banner_url,
            "shop_logo_url": s.shop_logo.url if s.shop_logo else "",
            "bio": s.shop_or_bio,
            "location": ", ".join([x for x in [s.city, s.region, s.country] if x]),
            "sales_count": s.sales_count,
            "followers_count": s.followers_count,
            "products": ProductSerializer(prods, many=True).data
        })
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def currency_rates_api(request):
    try:
        req = urllib.request.urlopen("https://open.er-api.com/v6/latest/PHP", timeout=3)
        data = json.loads(req.read().decode('utf-8'))
        return Response({"source": "Live ExchangeRate API", "USD": data["rates"].get("USD", 0.0172)})
    except Exception:
        return Response({"source": "Offline VM Fallback Rate", "USD": 0.0172})


class UserProfileViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class ProductViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = DigitalProduct.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = DigitalProduct.objects.all().order_by('-id')
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        if search:
            qs = qs.filter(title__icontains=search)
        if category and category != 'All':
            qs = qs.filter(category__icontains=category)
        return qs

    def perform_create(self, serializer):
        files = self.request.FILES.getlist('images')[:10]
        single_img = self.request.FILES.get('image')
        first_img = files[0] if files else single_img
        product = serializer.save(seller=self.request.user, image=first_img)
        for f in files[1:]:
            ProductImage.objects.create(product=product, image=f)

    def perform_update(self, serializer):
        photo_order_raw = self.request.data.get('photo_order')
        files = self.request.FILES.getlist('images')[:10]
        single_img = self.request.FILES.get('image')

        if photo_order_raw:
            product = serializer.save()
            try:
                manifest = json.loads(photo_order_raw)

                existing_file_map = {}
                if product.image:
                    try:
                        product.image.seek(0)
                        existing_file_map[product.image.url] = (
                            product.image.name.split('/')[-1],
                            ContentFile(product.image.read())
                        )
                    except Exception:
                        pass

                for extra in product.extra_images.all():
                    if extra.image:
                        try:
                            extra.image.seek(0)
                            existing_file_map[extra.image.url] = (
                                extra.image.name.split('/')[-1],
                                ContentFile(extra.image.read())
                            )
                        except Exception:
                            pass

                ordered_items = []
                for entry in manifest[:10]:
                    etype = entry.get('type')
                    if etype == 'existing':
                        raw_url = entry.get('url', '')
                        norm_url = raw_url if raw_url.startswith(('http://', 'https://', '/')) else f'/{raw_url}'
                        if norm_url in existing_file_map:
                            ordered_items.append(('file', existing_file_map[norm_url]))
                        elif raw_url in existing_file_map:
                            ordered_items.append(('file', existing_file_map[raw_url]))
                        elif raw_url.startswith(('http://', 'https://')):
                            ordered_items.append(('url', raw_url))
                    elif etype == 'new':
                        idx = entry.get('index', -1)
                        if 0 <= idx < len(files):
                            f = files[idx]
                            ordered_items.append(('file', (f.name, f)))

                product.extra_images.all().delete()
                if product.image:
                    product.image.delete(save=False)
                    product.image = None

                url_slots = []
                primary_set = False

                for kind, payload in ordered_items:
                    if kind == 'file':
                        fname, fcontent = payload
                        if not primary_set:
                            product.image.save(fname, fcontent, save=False)
                            primary_set = True
                        else:
                            extra_obj = ProductImage(product=product)
                            extra_obj.image.save(fname, fcontent, save=True)
                    elif kind == 'url':
                        url_slots.append(payload)

                if not primary_set and url_slots:
                    product.image_url = url_slots[0]
                    product.image_url_2 = url_slots[1] if len(url_slots) > 1 else ''
                    product.image_url_3 = url_slots[2] if len(url_slots) > 2 else ''
                elif primary_set:
                    product.image_url_2 = url_slots[0] if len(url_slots) > 0 else ''
                    product.image_url_3 = url_slots[1] if len(url_slots) > 1 else ''

                product.save()
                return
            except Exception:
                pass

        if files:
            product = serializer.save(image=files[0])
            product.extra_images.all().delete()
            for f in files[1:]:
                ProductImage.objects.create(product=product, image=f)
        elif single_img:
            serializer.save(image=single_img)
        else:
            serializer.save()


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
            return Response({"error": "Insufficient Suki Wallet credits."}, status=status.HTTP_400_BAD_REQUEST)

        created_orders = []
        for item in cart_items:
            product = item.product
            if product.stock_licenses < item.quantity:
                return Response({"error": f"Out of stock: {product.title}"}, status=status.HTTP_400_BAD_REQUEST)
            product.stock_licenses -= item.quantity
            product.save()

            seller = product.seller
            seller.suki_wallet_balance += (product.price * item.quantity)
            seller.sales_count += item.quantity
            seller.save()

            order = Order.objects.create(
                customer=customer,
                product=product,
                selected_size=item.selected_size or "Standard Digital",
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
        if order.product.seller != request.user:
            return Response({'error': 'Not authorized to fulfill this order.'}, status=status.HTTP_403_FORBIDDEN)

        custom_link = (request.data.get('delivery_link') or '').strip()
        seller_note = (request.data.get('seller_note') or '').strip()
        final_link = custom_link or order.product.download_link

        if custom_link and custom_link != order.product.download_link:
            order.product.download_link = custom_link
            order.product.save(update_fields=['download_link'])

        order.status = 'DELIVERED'
        order.save()

        recipient = order.customer.email or f"{order.customer.username}@suki.ph"
        shop_name = order.product.seller.shop_name or order.product.seller.username
        email_body = (
            f"Hi {order.customer.first_name or order.customer.username},\n\n"
            f"Thank you for your order ({order.delivery_tracking_code}) from {shop_name}!\n\n"
            f"--- OFFICIAL DIGITAL DELIVERY RECEIPT ---\n"
            f"Tracking Code: {order.delivery_tracking_code}\n"
            f"Product: {order.product.title} ({order.selected_size})\n"
            f"Amount Paid: PHP {order.total_amount}\n"
            f"Access your template / digital file here: {final_link}\n"
        )
        if seller_note:
            email_body += f"\nSeller Note: {seller_note}\n"
        email_body += "\nYou can also view this receipt and open your link anytime inside your Suki Completed Orders dashboard."

        try:
            send_mail(
                subject=f"[Suki Receipt #{order.delivery_tracking_code}] Your Digital Product is Ready: {order.product.title}",
                message=email_body,
                from_email='delivery@suki-marketplace.ph',
                recipient_list=[recipient],
                fail_silently=True,
            )
        except Exception:
            pass

        serializer = self.get_serializer(order)
        return Response({
            'message': f'Template link automatically sent to {recipient} and order marked as Completed!',
            'tracking': order.delivery_tracking_code,
            'recipient_email': recipient,
            'order': serializer.data
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