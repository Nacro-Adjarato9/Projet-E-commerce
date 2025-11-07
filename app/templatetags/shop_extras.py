from django import template
import random

register = template.Library()

@register.filter
def split(value, arg):
    """Split a string by the given separator"""
    return value.split(arg)

@register.filter
def random_item(value):
    """Return a random item from a list"""
    try:
        return random.choice(value)
    except (IndexError, TypeError):
        return ''

@register.filter
def get_random_default_image(value):
    """Get a random default product image"""
    default_images = [
        'shop-1.jpg',
        'shop-2.jpg',
        'shop-3.jpg',
        'shop-4.jpg',
        'shop-5.jpg',
        'armoir.jpeg',
        'meublee.jpeg',
        'table.jpeg'
    ]
    return random.choice(default_images)
