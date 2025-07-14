from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key.
    Usage: {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None

    try:
        return dictionary.get(str(key))
    except (KeyError, AttributeError):
        return None
