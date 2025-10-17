# accounts/views.py
import traceback
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator

from .forms import SignUpForm, LoginForm, UserForm, ProfileForm
from .models import Profile
from django.contrib.auth import logout
from .subscriptions import get_subscription_features

import random

User = get_user_model()

# ------------------------------
# Authentication Views
# ------------------------------

from django.contrib import messages
from django.contrib.auth import login, get_backends
from django.shortcuts import render, redirect
from .forms import SignUpForm

def signup_view(request):
    """User signup view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)
            messages.success(request, "Account created successfully! Welcome aboard 🎉")
            return redirect('accounts:onboarding')
        else:
            messages.error(request, "There was a problem creating your account. Please check the form and try again.")
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup_page.html', {'form': form})

from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    # If it's an AJAX (JS) request:
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        if form.is_valid():
            login(request, form.get_user())
            return JsonResponse({"success": True, "redirect": "/dashboard/"})
        else:
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({"success": False, "errors": errors}, status=200)  # ✅ Use 200, not 400

    # If it's a regular form POST (HTML)
    elif request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Welcome back! You’ve successfully logged in.")
            return redirect("/dashboard/")
        else:
            # This is what shows an error message to the user
            messages.error(request, "Incorrect email or password. Please try again.")

    # Render the page normally
    return render(request, "accounts/login_page.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('index')
    
# ------------------------------
# Email Verification Helpers
# ------------------------------

# CHANGE IN PRODUCTION
def send_verification_code(request):
    """Generate a 6-digit code and store in session (for dev/testing)."""
    code = random.randint(100000, 999999)
    request.session['email_verification_code'] = str(code)
    request.session['email_verification_user'] = request.user.id
    print(f"[DEV] Verification code: {code}")  # For dev only; in prod, send email


# ------------------------------
# User Settings Page
# ------------------------------

@login_required
def settings_page(request):
    """Profile, password, and subscription settings."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    # Initialize forms with current data
    user_form = UserForm(instance=user)
    profile_form = ProfileForm(instance=profile)
    pwd_form = PasswordChangeForm(user=user)

    if request.method == "POST":
        # ------------------------
        # Email verification AJAX
        # ------------------------
        if "send_verification_code" in request.POST:
            send_verification_code(request)
            return JsonResponse({"status": "ok"})

        elif "verify_code" in request.POST:
            entered_code = request.POST.get("code")
            session_code = request.session.get("email_verification_code")
            if entered_code == session_code:
                user.is_email_verified = True
                user.save()
                request.session.pop("email_verification_code", None)
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse({"status": "error", "message": "Incorrect code"})

        # ------------------------
        # Profile update
        # ------------------------
        elif "update_profile" in request.POST:
            user_form = UserForm(request.POST, instance=user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("accounts:settings")

        # ------------------------
        # Password change
        # ------------------------
        elif "change_password" in request.POST:
            pwd_form = PasswordChangeForm(user, request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Password changed successfully!")
                return redirect("accounts:settings")
            else:
                messages.error(request, "Please correct the errors below.")

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "pwd_form": pwd_form,
        "ai_credits": user.ai_credits,
        "current_plan": user.current_subscription.plan.name if user.current_subscription else "Free",
        "plan_end": user.current_subscription.end_date if user.current_subscription else None,
    }

    return render(request, "accounts/settings.html", context)


# ------------------------------
# Email Verification Link
# ------------------------------

def verify_email(request, uidb64, token):
    """Verify user email from a link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.success(request, "Your email has been verified!")
        return redirect("dashboard")
    else:
        messages.error(request, "Invalid or expired verification link.")
        return redirect("accounts:signup")

# ------------------------------
# Subscription Management
# ------------------------------

import stripe
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, reverse
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import SubscriptionPlan, UserSubscription, CustomUser

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def subscriptions(request):
    plans = SubscriptionPlan.objects.all()
    current_sub = request.user.current_subscription

    # Determine if user already had a free trial
    # (You can check if they ever had a subscription of a paid plan)
    had_trial = UserSubscription.objects.filter(
        user=request.user,
        plan__name__in=['Premium', 'Pro']
    ).exists()

    monthly_plans = plans.filter(duration_days=30)
    yearly_plans = plans.filter(duration_days=365)

    for plan in plans:
        plan.features_list = [f.strip() for f in plan.features.split(',')] if plan.features else []
        plan.non_features_list = [f.strip() for f in plan.non_features.split(',')] if plan.non_features else []

    context = {
        'monthly_plans': monthly_plans,
        'yearly_plans': yearly_plans,
        'current_subscription': current_sub,
        'had_trial': had_trial,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'accounts/subscriptions/subscriptions.html', context)



@require_POST
@login_required
def create_checkout_session(request, plan_id):
    """Create Stripe checkout session (with debug logging)"""

    trial_days = 14 # Change as needed
    # later add discount percentage

    try:

        plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
        user = request.user

        # Ensure Stripe Customer exists
        if not user.stripe_customer_id:
            user.create_stripe_customer()

        success_url = f"{settings.SITE_URL}{reverse('accounts:checkout_success')}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.SITE_URL}{reverse('accounts:checkout_cancel')}"

        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,  # must be >= 1
            }],
            mode='subscription',
            subscription_data={
                'trial_period_days': trial_days
            },
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user.id),
                'plan_id': str(plan.id)
            },
        )

        print("[DEBUG] Checkout session successfully created.")
        print(f"[DEBUG] Session ID: {session.id}")
        print("=== Stripe Checkout Session Debug End ===\n")

        return JsonResponse({'sessionId': session.id})

    except Exception as e:
        print("\n❌ Stripe Checkout Error:", str(e))
        print(traceback.format_exc())
        print("=== Stripe Checkout Session Debug End (ERROR) ===\n")
        return JsonResponse({'error': str(e)}, status=400)



@login_required
def checkout_success(request):
    """Handle successful checkout"""
    session_id = request.GET.get('session_id')
    context = {
        'session_id': session_id,
        'message': 'Subscription activated successfully!'
    }
    return render(request, 'accounts/subscriptions/success.html', context)


@login_required
def checkout_cancel(request):
    """Handle cancelled checkout"""
    context = {
        'message': 'Checkout was cancelled. You have not been charged.'
    }
    return render(request, 'accounts/subscriptions/cancel.html', context)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponseBadRequest('Invalid payload')
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest('Invalid signature')

    event_type = event['type']
    data = event['data']['object']

    # Handle checkout completion
    if event_type == 'checkout.session.completed':
        handle_checkout_completed(data)
    
    # Handle successful payment
    elif event_type == 'invoice.payment_succeeded':
        handle_payment_succeeded(data)
    
    # Handle failed payment
    elif event_type == 'invoice.payment_failed':
        handle_payment_failed(data)
    
    # Handle subscription updates/deletions
    elif event_type in ('customer.subscription.deleted', 'customer.subscription.updated'):
        handle_subscription_changed(data)

    return HttpResponse(status=200)


def handle_checkout_completed(session):
    """Process completed checkout session"""
    stripe_sub_id = session.get('subscription')
    stripe_customer_id = session.get('customer')

    if stripe_sub_id:
        sub = stripe.Subscription.retrieve(stripe_sub_id)
        price_id = sub['items']['data'][0]['price']['id']
        
        plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()
        user = CustomUser.objects.filter(stripe_customer_id=stripe_customer_id).first()
        
        if user and plan:
            UserSubscription.objects.update_or_create(
                stripe_subscription_id=stripe_sub_id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'stripe_customer_id': stripe_customer_id,
                    'is_active': True,
                    'start_date': timezone.now(),
                    'end_date': timezone.datetime.fromtimestamp(
                        sub['current_period_end'], tz=timezone.utc
                    ),
                }
            )


def handle_payment_succeeded(invoice):
    """Process successful payment"""
    sub_id = invoice.get('subscription')
    if sub_id:
        sub = stripe.Subscription.retrieve(sub_id)
        user_sub = UserSubscription.objects.filter(stripe_subscription_id=sub_id).first()
        
        if user_sub:
            user_sub.is_active = True
            user_sub.end_date = timezone.datetime.fromtimestamp(
                sub['current_period_end'], tz=timezone.utc
            )
            user_sub.save(update_fields=['is_active', 'end_date'])


def handle_payment_failed(invoice):
    """Process failed payment"""
    sub_id = invoice.get('subscription')
    if sub_id:
        user_sub = UserSubscription.objects.filter(stripe_subscription_id=sub_id).first()
        if user_sub:
            user_sub.is_active = False
            user_sub.save(update_fields=['is_active'])


def handle_subscription_changed(subscription):
    """Process subscription update or deletion"""
    sub_id = subscription.get('id')
    user_sub = UserSubscription.objects.filter(stripe_subscription_id=sub_id).first()
    
    if user_sub:
        status = subscription.get('status')
        user_sub.is_active = status in ('active', 'trialing')
        user_sub.end_date = timezone.datetime.fromtimestamp(
            subscription['current_period_end'], tz=timezone.utc
        )
        user_sub.save(update_fields=['is_active', 'end_date'])


@login_required
@require_POST
def cancel_subscription(request):
    """Cancel user's active subscription"""
    current_sub = request.user.current_subscription
    
    if not current_sub:
        return JsonResponse({'error': 'No active subscription found'}, status=400)
    
    try:
        # Cancel at period end (don't refund)
        stripe.Subscription.modify(
            current_sub.stripe_subscription_id,
            cancel_at_period_end=True
        )
        return JsonResponse({'message': 'Subscription will cancel at period end'})
    
    except Exception as e:
        print("Stripe Checkout Error: ", str(e))
        return JsonResponse({'error': str(e)}, status=400)

from django.http import JsonResponse
from django.contrib.auth import authenticate
import json

@login_required
def verify_password(request):
    if request.method == "POST":
        data = json.loads(request.body)
        password = data.get("password", "")
        user = authenticate(username=request.user.username, password=password)
        return JsonResponse({"valid": user is not None})
    return JsonResponse({"error": "Invalid request"}, status=400)

from .forms import OnboardingForm, GOAL_CHOICES, REFERRAL_CHOICES
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import redirect

@login_required
def onboarding_view(request):
    if request.method == "POST":
        form = OnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            selected_goals = form.cleaned_data.get("goals_interests", [])
            other = form.cleaned_data.get("other_interest")
            if other:
                selected_goals.append(other)
            user.goals_interests = ", ".join(selected_goals)

            referral = form.cleaned_data.get("referral_source")
            referral_other = form.cleaned_data.get("referral_other")
            user.referral_source = referral_other if referral == "other" else referral

            user.save()

            # ✅ If AJAX request, send JSON instead of redirect
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "redirect": "/dashboard/"})
            
            return redirect("dashboard")

        # invalid form
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = OnboardingForm(instance=request.user)

    context = {
        "form": form,
        "GOAL_CHOICES": GOAL_CHOICES,
        "REFERRAL_CHOICES": REFERRAL_CHOICES,
        "subscription_features": get_subscription_features(),
    }
    return render(request, "accounts/onboarding.html", context)

@login_required
def customer_portal(request):
    user = request.user
    customer_id = user.create_stripe_customer()  # ensures they have one

    # Create the portal session
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri('/dashboard/'),  # where Stripe redirects after they're done
        # Possibly change return URL
    )

    return redirect(session.url)