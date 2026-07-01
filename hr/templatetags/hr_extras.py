from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, 0)

@register.filter
def mod(value, arg):
    """Return value % arg — used for cycling CSS classes."""
    try:
        return int(value) % int(arg)
    except (ValueError, ZeroDivisionError):
        return 0