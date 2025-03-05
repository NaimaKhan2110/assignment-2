from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Check if the user is part of a specific group."""
    return user.groups.filter(name=group_name).exists()
