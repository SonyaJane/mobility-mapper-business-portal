from django import template

register = template.Library()

@register.filter
def device_labels(devices):
    """
    Convert a list of mobility device keys to their display names.
    """
    from accounts.models import UserProfile
    choices_dict = dict(UserProfile.MOBILITY_DEVICE_CHOICES)
    # Use list of labels, defaulting to key if not found
    # Exclude generic 'other' key; handle actual text separately
    labels = [choices_dict.get(dev, dev) for dev in (devices or []) if dev != 'other']
    return ", ".join(labels)

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
