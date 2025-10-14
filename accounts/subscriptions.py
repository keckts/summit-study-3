def get_subscription_features():
    # (feature_text, available_bool, plan)
    # this func allows you to easily update features in one place
    features = [
        ("10k credits per day", True, "free"),
        ("Practice Test generation", True, "free"),
        ("Flashcard generation", True, "free"),
        ("Writing Task AI feedback", True, "free"),
        ("AI Chatbot", True, "free"),
        ("No Program Access", False, "free"),
        ("No Progress Tracking", False, "free"),
        ("No access to early features", False, "free"),

        ("300k credits per month", True, "premium"),
        ("Everything in Free Plan", True, "premium"),
        ("Progress Tracking", True, "premium"),
        ("Access to 3 programs per month", True, "premium"),
        ("Access to early features", False, "premium"),
        ("Advanced progress tracking", False, "premium"),

        ("Everything in Premium", True, "pro"),
        ("1 million credits per month", True, "pro"),
        ("Unlimited Program Access", True, "pro"),
        ("Access to early features", True, "pro"),
    ]

    def render_features_html(plan):
        """Return HTML list items for the given plan."""
        items = []
        for text, available, fplan in features:
            if fplan == plan:
                icon = '<i class="fas fa-check-circle"></i>' if available else '<i class="fas fa-xmark"></i>'
                items.append(f"<li>{icon} {text}</li>")
        return "\n".join(items)

    free_features_html = render_features_html("free")
    premium_features_html = render_features_html("premium")
    pro_features_html = render_features_html("pro")

    return f"""
  <section class="pricing" id="pricing">
    <div class="section-header">
      <span class="section-badge">Pricing Plans</span>
      <h2>Choose Your Path to Success</h2>
      <p>Flexible plans designed for every student's needs and budget</p>
      <div style="margin-top: 10px; display: flex; justify-content: center; gap: 10px;">
        <button id="annual-btn" class="toggle-btn active">Annual</button>
        <button id="monthly-btn" class="toggle-btn">Monthly</button>
      </div>
    </div>
    <div class="pricing-grid">

      <!-- Free Plan -->
      <div class="pricing-card">
        <h3>Free</h3>
        <div class="pricing-price">$0<span>/mth</span></div>
        <p class="pricing-period">Perfect for getting started</p>
        <ul class="pricing-features">
          {free_features_html}
        </ul>
        <a href="{{% url 'accounts:signup_view' %}}" class="btn btn-secondary pricing-btn">Get Started</a>
      </div>

      <!-- Premium Plan -->
      <div class="pricing-card featured">
        <div class="pricing-badge">Most Popular</div>
        <h3>Premium</h3>
        <div class="pricing-price" id="premium-price">$9.6<span>/mth</span></div>
        <p class="pricing-period" id="premium-period">Or $115.2 per year (Save 20%)</p>
        <ul class="pricing-features">
          {premium_features_html}
        </ul>
        <a href="{{% url 'accounts:signup_view' %}}" class="btn btn-primary pricing-btn">Get Premium</a>
      </div>

      <!-- Pro Plan -->
      <div class="pricing-card">
        <h3>Pro</h3>
        <div class="pricing-price" id="pro-price">$20<span>/mth</span></div>
        <p class="pricing-period" id="pro-period">Or $240 per year (Save 20%)</p>
        <ul class="pricing-features">
          {pro_features_html}
        </ul>
        <a href="{{% url 'accounts:signup_view' %}}" class="btn btn-primary pricing-btn">Get Pro</a>
      </div>

    </div>
  </section>
  """


from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def subscription_required(view_func):
    """Decorator to ensure the user has an active subscription."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Redirect to login if user is not authenticated
        if not request.user.is_authenticated:
            login_url = reverse('accounts:login')
            return redirect(f"{login_url}?next={request.path}")

        # Check if the user has a subscription and if it's active
        subscription = getattr(request.user, "subscription", None)
        if not subscription or not subscription.is_active:
            return redirect(reverse("accounts:subscriptions"))

        # Otherwise, proceed with the view
        return view_func(request, *args, **kwargs)
    return _wrapped_view
