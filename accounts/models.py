from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# -------------------
# User
# -------------------
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with only an email and password."""
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
        """Create and save a superuser with only email and password."""
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

    goals = models.TextField(blank=True, null=True, help_text="Comma-separated list of user's goals/interests")
    referral_source = models.CharField(max_length=100, blank=True, null=True)
    referral_other = models.CharField(max_length=200, blank=True, null=True)

    # inside CustomUser (models.py)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or self.email

    def generate_username(self):
        """Generate username from email if blank"""
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

    @property
    def current_subscription(self):
        return self.usersubscription_set.filter(is_active=True, end_date__gt=timezone.now()).first()

    def save(self, *args, **kwargs):
        if not self.username:
            self.generate_username()
        super().save(*args, **kwargs)

# models.py (near CustomUser)
import stripe
from django.conf import settings

def create_stripe_customer(self):
    if self.stripe_customer_id:
        return self.stripe_customer_id
    stripe.api_key = settings.STRIPE_SECRET_KEY
    customer = stripe.Customer.create(email=self.email, metadata={"user_id": self.id})
    self.stripe_customer_id = customer["id"]
    self.save(update_fields=["stripe_customer_id"])
    return self.stripe_customer_id

CustomUser.create_stripe_customer = create_stripe_customer


# -------------------
# Profile
# -------------------
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# ----------------
# Onboarding
# ----------------
class Onboarding(models.Model):
    user = models.OneToOneField("accounts.CustomUser", on_delete=models.CASCADE)
    referral_source = models.CharField(max_length=255)  # stores selected or typed referral
    goals_interests = models.TextField(null=True, blank=True)  # comma-separated or JSON list

    def __str__(self):
        return f"Onboarding for {self.user.username or self.user.email}"



# -------------------
# Subscription
# -------------------
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    stripe_price_id = models.CharField(max_length=100)
    duration_days = models.IntegerField()  # e.g., 30 for monthly
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    @property
    def is_current(self):
        return self.is_active and self.end_date > timezone.now()
