from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
import stripe
from django.conf import settings

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if not user.username:
            user.generate_username()
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    points = models.IntegerField(default=0)
    ai_credits = models.IntegerField(default=10000)
    is_email_verified = models.BooleanField(default=False)
    goals = models.TextField(blank=True, null=True)
    referral_source = models.CharField(max_length=100, blank=True, null=True)
    referral_other = models.CharField(max_length=200, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or self.email

    def generate_username(self):
        if self.username:
            return
        base_username = self.email.split('@')[0]
        username = base_username
        counter = 1
        while self.__class__.objects.filter(username=username).exists() and counter < 10000:
            username = f"{base_username}{counter}"
            counter += 1
        if counter >= 10000:
            import uuid
            username = f"user_{uuid.uuid4().hex[:8]}"
        self.username = username

    def create_stripe_customer(self):
        """Create or return existing Stripe customer ID"""
        if self.stripe_customer_id:
            return self.stripe_customer_id
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customer = stripe.Customer.create(
            email=self.email,
            metadata={"user_id": self.id}
        )
        self.stripe_customer_id = customer["id"]
        self.save(update_fields=["stripe_customer_id"])
        return self.stripe_customer_id

    @property
    def current_subscription(self):
        """Get active subscription"""
        return self.usersubscription_set.filter(
            is_active=True, 
            end_date__gt=timezone.now()
        ).first()

    def save(self, *args, **kwargs):
        if not self.username:
            self.generate_username()
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Onboarding(models.Model):
    user = models.OneToOneField("accounts.CustomUser", on_delete=models.CASCADE)
    referral_source = models.CharField(max_length=255)
    goals_interests = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Onboarding for {self.user.username or self.user.email}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=100, unique=True)
    duration_days = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True, help_text="List of features separated by comments e.g.")
    non_features = models.TextField(blank=True, null=True, help_text="List of non-features e.g 'No priority support'")

    def __str__(self):
        return self.name

    @property
    def get_monthly_price(self):
        
        if self.duration_days == 30:
            return f"{self.price:.2f}"
        elif self.duration_days == 365:
            monthly_price = (self.price / Decimal(12)) * Decimal('0.8')
            return f"{monthly_price:.2f}"



    class Meta:
        ordering = ['price']


class UserSubscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    @property
    def is_current(self):
        return self.is_active and self.end_date > timezone.now()

    class Meta:
        ordering = ['-created_at']