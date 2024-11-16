from django import template

register = template.Library()


@register.simple_tag
def has_perm(user, perm):
    """
    This template tag checks if the given user has a specific permission.

    Args:
        user (User): The user whose permissions you want to check.
        perm (Permission): The permission you want to check.

    Returns:
        bool: True if the user has the specified permission; otherwise, False.

    Example:
        {% has_perm user "my_app.view_mymodel" %}

    """
    return user.has_perm(perm)


@register.simple_tag
def has_role(user, role):
    """
    This template tag checks if the given user has a specific role.

    Args:
        user (User): The user whose roles you want to check.
        role (Union[str, Role]): The role you want to check.

    Returns:
        bool: True if the user has the specified role; otherwise, False.

    Example:
        {% has_role user "some_role" %}
    """
    return user.has_role(role)


@register.simple_tag
def has_active_session(user):
    """
    This template tag checks if the given user has an active session.

    Args:
        user (User): The user whose session you want to check for activity.

    Returns:
        bool: True if the user has an active session; otherwise, False.

    Example:
        {% has_active_session user %}
    """
    return user.has_active_session()
