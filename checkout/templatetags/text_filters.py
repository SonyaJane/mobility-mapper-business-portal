from django import template

register = template.Library()

@register.filter
def lcfirst(value):
    """Lowercase only the first character of the string."""
    if not value:
        return value
    s = str(value)
    return s[0].lower() + s[1:]