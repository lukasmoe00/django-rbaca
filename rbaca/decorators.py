from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url


def user_passes_test(
    test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    """
    Decorator that checks if the user passes a custom test function, otherwise redirects to a specified login page.

    Args:
        test_func (Function): A callable that takes the user and additional keyword arguments and returns
            True if the user passes the test.
        login_url (str): The URL where the user will be redirected if the test fails.
        redirect_field_name (str): The name of the redirect field in the query string.

    Returns:
        A decorator function.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user, kwargs):
                return view_func(request, *args, **kwargs)

            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]

            if (not login_scheme or login_scheme == current_scheme) and (
                not login_netloc or login_netloc == current_netloc
            ):
                path = request.get_full_path()

            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(path, resolved_login_url, redirect_field_name)

        return _wrapped_view

    return decorator


def session_required(redirect_field_name=REDIRECT_FIELD_NAME, session_url=None):
    """
    Decorator that checks if the user has an active session or is a superuser,
    otherwise redirects to a specified login page.

    Args:
        redirect_field_name (str): The name of the redirect field in the query string.
        session_url (str): The URL where the user will be redirected if the session check fails.

    Returns:
        A decorator function.
    """
    if getattr(settings, "USE_SESSIONS", False):
        return user_passes_test(
            lambda u, k: u.has_active_session() or u.is_superuser,
            login_url=session_url,
            redirect_field_name=redirect_field_name,
        )
    return user_passes_test(lambda u, k: True)


def role_required(role, login_url=None, raise_exception=False):
    """
    Decorator that checks if the user has a specific role, otherwise redirects to a specified
    login page or raises a PermissionDenied exception.

    Args:
        role (Union[Role, str]): The name of the role that the user must have.
        login_url (str): The URL where the user will be redirected if they don't have the required role.
        raise_exception (bool): If True, a PermissionDenied exception is raised instead of a redirect.

    Returns:
        A decorator function.
    """

    def check_role(user, kwargs=None):
        if user.has_role(role):
            return True

        if raise_exception:
            raise PermissionDenied

        return False

    return user_passes_test(check_role, login_url=login_url)


def attribute_required(check_attribute, login_url=None, raise_exception=False):
    """
    Decorator that checks if a custom attribute check function returns True for the user,
    otherwise redirects to a specified login page or raises a PermissionDenied exception.

    Args:
        check_attribute (Function): A callable that takes the user and additional keyword arguments and
            returns True if the user passes the attribute check.
        login_url (str): The URL where the user will be redirected if the attribute check fails.
        raise_exception (bool): If True, a PermissionDenied exception is raised instead of a redirect.

    Returns:
        A decorator function.
    Example:
        @attribute_required(check_attribute=lambda u, k: True if u.id in k else False)
    """
    return user_passes_test(check_attribute, login_url=login_url)
