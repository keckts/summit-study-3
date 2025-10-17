from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup-page/', views.signup_view, name='signup_view'),
    path('login-page/', views.login_view, name='login_view'),
    path('settings/', views.settings_page, name='settings'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('logout-page/', views.logout_view, name='logout'),
    path('onboarding/', views.onboarding_view, name='onboarding'),

    path('verify-password/', views.verify_password, name='verify_password'),

    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('subscriptions/checkout/<int:plan_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('subscriptions/success/', views.checkout_success, name='checkout_success'),
    path('subscriptions/cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('subscriptions/cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    
    # Webhook (no authentication required)
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('customer-portal/', views.customer_portal, name='customer_portal'),
    
]