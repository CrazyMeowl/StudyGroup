from django import template

register = template.Library()

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ''
    
@register.filter
def contains(value, the_list):
    """Return True if value is in the_list (for use in templates)."""
    return value in the_list