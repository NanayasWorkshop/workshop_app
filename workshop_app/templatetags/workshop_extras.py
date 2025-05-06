from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    try:
        # First try to get the attribute directly
        return obj.__getattribute__(attr)
    except AttributeError:
        # If that fails, try to get it from the form fields
        if hasattr(obj, 'fields') and attr in obj.fields:
            return obj[attr]
        # If all else fails, re-raise the original exception
        raise
