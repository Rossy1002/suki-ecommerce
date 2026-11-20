from django.contrib import admin
from .models import User, DigitalProduct, Wishlist, CartItem, Order, Review, SupportTicket

admin.site.register([User, DigitalProduct, Wishlist, CartItem, Order, Review, SupportTicket])
