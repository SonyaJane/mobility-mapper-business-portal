from django import template
import datetime

register = template.Library()


@register.filter
def format_time(value):
    """
    Converts a time string in 24-hour HH:MM format to 12-hour format with am/pm.
    For example, "09:00" -> "9:00 am", "15:30" -> "3:30 pm".
    """
    if not value:
        return ''
    try:
        # Parse the string assuming HH:MM format
        dt = datetime.datetime.strptime(value, "%H:%M")
        # Strip leading zeros from hour
        hour = dt.strftime("%I").lstrip('0')
        minute = dt.strftime("%M")
        suffix = dt.strftime("%p").lower()
        return f"{hour}:{minute} {suffix}"
    except (ValueError, TypeError):
        # If parsing fails, return original value
        return value
