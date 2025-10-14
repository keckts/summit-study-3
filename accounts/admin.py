from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserSubscription, SubscriptionPlan


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Onboarding Info", {"fields": ("goals", "referral_source", "referral_other")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Onboarding Info", {"fields": ("goals", "referral_source", "referral_other")}),
    )

admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)