from django import template

register = template.Library()

@register.filter
def device_labels(devices):
    """
    Convert a list of mobility device keys to their display labels.
    """
    # devices may be a manager or iterable of MobilityDevice instances or their PKs
    devices_qs = devices.all() if hasattr(devices, 'all') else devices or []
    # Collect device labels, excluding 'other'
    labels = []
    for dev in devices_qs:
        # dev may be instance or simple value
        label = getattr(dev, 'label', None)
        name = getattr(dev, 'name', None)
        if name == 'other':
            continue
        if label:
            labels.append(label)
        else:
            labels.append(str(dev))
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
