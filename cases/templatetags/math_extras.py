"""
Custom template filters for mathematical operations and utility functions
"""

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide two numbers"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage of value out of total"""
    try:
        if float(total) == 0:
            return 0
        result = (float(value) / float(total)) * 100
        return min(100, max(0, result))  # Clamp between 0 and 100
    except (ValueError, TypeError):
        return 0


@register.filter
def progress_bar_width(collected, target):
    """Calculate progress bar width as a percentage"""
    try:
        if float(target) == 0:
            return 0
        result = (float(collected) / float(target)) * 100
        return min(100, max(0, result))  # Clamp between 0 and 100
    except (ValueError, TypeError):
        return 0


@register.filter
def days_remaining(end_date):
    """Calculate days remaining until end_date"""
    try:
        from django.utils import timezone

        now = timezone.now()
        if hasattr(end_date, "date"):
            end_date = end_date.date()
        if hasattr(now, "date"):
            now = now.date()

        delta = end_date - now
        return max(0, delta.days)
    except (AttributeError, TypeError):
        return 0


@register.filter
def format_currency(value):
    """Format currency with Rs prefix"""
    try:
        value = float(value)
        if value >= 1000000:
            return f"Rs {value/1000000:.1f}M"
        elif value >= 1000:
            return f"Rs {value/1000:.0f}K"
        else:
            return f"Rs {value:.0f}"
    except (ValueError, TypeError):
        return "Rs 0"


@register.filter
def score_percentage(value):
    """Convert score to percentage"""
    try:
        return f"{float(value)*100:.0f}"
    except (ValueError, TypeError):
        return "0"
