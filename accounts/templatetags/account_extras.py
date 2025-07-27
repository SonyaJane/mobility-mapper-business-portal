from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)

# Custom filter to pre-filter unverified businesses
@register.filter
def filter_unverified(businesses, verification_status):
    """
    Returns only businesses that are not verified according to verification_status dict.
    """
    return [b for b in businesses if not verification_status.get(b.id)]
