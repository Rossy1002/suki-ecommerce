import uuid
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

User = get_user_model()


class SukiSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        # If this social account is already linked, let allauth proceed
        if sociallogin.is_existing:
            return

        # Automatically link to an existing user with the same verified email
        email = (
            sociallogin.user.email
            or sociallogin.account.extra_data.get('email', '')
        ).strip()
        if not email:
            return

        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user:
            sociallogin.connect(request, existing_user)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        email = (data.get('email') or '').strip()
        base = slugify(email.split('@')[0]) if email else 'suki_buyer'
        user.username = f"{base}_{uuid.uuid4().hex[:4]}"
        user.email = email
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.role = 'customer'
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not getattr(user, 'role', None):
            user.role = 'customer'
        if getattr(user, 'suki_wallet_balance', 0) == 0:
            user.suki_wallet_balance = 1000.00
        user.save()
        return user