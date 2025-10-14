from django import template

register = template.Library()

@register.filter
def format_credits(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value  # fallback, just return as-is

    if value >= 1000:
        # e.g. 12345 -> "12.3k"
        if value % 1000 == 0:
            return f"{value // 1000}k"
        return f"{value/1000:.1f}k".rstrip('0').rstrip('.') + " credits"
    return f"{value} credits"
