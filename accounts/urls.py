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

    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('subscriptions/checkout/<int:plan_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('verify-password/', views.verify_password, name='verify_password'),
    
]