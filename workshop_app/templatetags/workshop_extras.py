from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    return obj.__getattribute__(attr)
