from django import template

register = template.Library()

@register.simple_tag
def rating_range(value):
    return range(1, value + 1)