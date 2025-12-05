"""
Template tags and filters for the reviews app.
"""

from django import template

register = template.Library()


@register.filter
def range_filter(min_val, max_val):
    """Generate a range from min_val to max_val (inclusive)."""
    return range(int(min_val), int(max_val) + 1)


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if dictionary and key:
        return dictionary.get(str(key))
    return None


@register.filter
def filter_required(queryset):
    """Filter queryset to only required items."""
    return queryset.filter(is_required=True)


@register.filter
def map_attr(queryset, attr):
    """Map queryset to list of attribute values."""
    return list(queryset.values_list(attr, flat=True))
