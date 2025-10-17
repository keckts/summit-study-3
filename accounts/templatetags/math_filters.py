from django import template

register = template.Library()

@register.filter
def divide(value, divisor):
    try:
        return round(float(value) / float(divisor), 2)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
