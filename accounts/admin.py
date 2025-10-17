from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserSubscription, SubscriptionPlan, Onboarding, Profile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'is_active', 'is_email_verified', 'current_subscription_display']
    list_filter = ['is_active', 'is_email_verified', 'is_staff']
    search_fields = ['email', 'username']
    readonly_fields = ['stripe_customer_id', 'date_joined', 'last_login']
    
    def current_subscription_display(self, obj):
        sub = obj.current_subscription
        return f"{sub.plan.name}" if sub else "None"
    current_subscription_display.short_description = 'Current Plan'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio']
    search_fields = ['user__email', 'user__username']


@admin.register(Onboarding)
class OnboardingAdmin(admin.ModelAdmin):
    list_display = ['user', 'referral_source']
    search_fields = ['user__email', 'user__username']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'stripe_price_id']
    
    list_editable = ['price']
    search_fields = ['name', 'stripe_price_id']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'price', 'duration_days')
        }),
        ('Stripe', {
            'fields': ('stripe_price_id',)
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as comma-separated values'
        }),
        ('Non-Features', {
            'fields': ('non_features',),
            'description': 'Enter non-features as comma-separated values'
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_active', 'plan', 'start_date']
    search_fields = ['user__email', 'user__username', 'stripe_subscription_id']
    readonly_fields = ['stripe_subscription_id', 'stripe_customer_id', 'start_date', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Subscription Info', {
            'fields': ('user', 'plan', 'is_active')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        ('Stripe', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id')
        }),
    )
    
    def is_current(self, obj):
        return obj.is_current
    is_current.boolean = True
    is_current.short_description = 'Currently Active'