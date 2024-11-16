from django.conf import settings
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured


class SessionRequiredMixin(AccessMixin):
    """
    This mixin checks whether a user has an active session and is designed to be used with views.

    Attributes:
        None

    Methods:
        has_session(self): Checks if the application uses sessions and if the user has an active session.
        dispatch(self, request, *args, **kwargs): Overrides the dispatch method to perform the session check.
    """

    def has_session(self):
        """
        Check if the application is configured to use sessions. If sessions are enabled,
        it verifies if the user has an active session.

        Returns:
            bool: True if sessions are not used or the user has an active session, otherwise False.
        """
        if getattr(settings, "USE_SESSIONS", False):
            return self.request.user.has_active_session()
        return True

    def dispatch(self, request, *args, **kwargs):
        """
        Overrides the dispatch method to check if the user has an active session. If not,
        it calls handle_no_permission(), indicating the user has no active session.
        If the user has an active session, it proceeds with the view execution.
        """
        if not self.has_session():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(AccessMixin):
    """
    This mixin checks whether a user has a specific role and is designed to be used with views.
    The 'role_required' attribute should be set on views using this mixin.

    Attributes:
        role_required (Union[List[Role], Role, List[str], str]): Defines which roles are required.

    Methods:
        get_role_required(self): Gets the 'role_required' attribute defined in the view and ensures it is a string.
        has_role(self): Checks if the user has the role specified by 'role_required'.
        dispatch(self, request, *args, **kwargs): Overrides the dispatch method to check if the user has the
        required role. If not, it calls handle_no_permission(), indicating the user lacks the required role.
        If the user has the role, it proceeds with the view execution.
    """

    role_required = None

    def get_role_required(self):
        """
        Get the 'role_required' attribute defined in the view and verify if it is a string.

        Returns:
            The 'role_required' string if set in the view.

        Raises:
            ImproperlyConfigured if 'role_required' is not defined in the view or is not a string.
        """
        if self.role_required is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                f"role_required attribute. Define "
                f"{self.__class__.__name__}.role_required."
            )
        if not isinstance(self.role_required, str):
            raise ValueError(
                "param 'role' needs to be str not %s", str(type(self.role_required))
            )

        else:
            role = self.role_required
        return role

    def has_role(self):
        """
        Check if the user has the role specified by 'role_required'.

        Returns:
            True if the user has the required role, otherwise False.
        """
        role = self.get_role_required()
        return self.request.user.has_role(role)

    def dispatch(self, request, *args, **kwargs):
        """
        Overrides the dispatch method to check if the user has the required role. If not,
        it calls handle_no_permission(), indicating the user lacks the required role.
        If the user has the role, it proceeds with the view execution.
        """
        if not self.has_role():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AttributeRequiredMixin(AccessMixin):
    """
    This mixin checks user attributes against a defined check function and is designed to be
    used with views. The 'check_func' attribute should be set on views using this mixin.

    Attributes:
        check_func (Function): The function that checks the required attributes.

    Methods:
        get_check_func(self): Gets the 'check_func' attribute defined in the view.
        check_attributes(self, user, kwargs): Calls the check function with user attributes and
            view's keyword arguments (kwargs) to determine if the attributes pass the check.
        dispatch(self, request, *args, **kwargs): Overrides the dispatch method to check user
            attributes using 'check_attributes'. If the attributes do not pass the check,
            it calls handle_no_permission. If they do, it proceeds with the view execution.
    Example:
        check_func = lambda u, k: True if u.id in k else False
    """

    check_func = None

    def get_check_func(self):
        """
        Get the 'check_func' attribute defined in the view.

        Returns:
            The 'check_func' attribute, which is a function responsible for checking user attributes.

        Raises:
            ImproperlyConfigured if 'check_func' is not defined in the view.
        """
        if self.check_func is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                f"check_func attribute. Define "
                f"{self.__class__.__name__}.check_func."
            )

        return self.check_func

    def check_attributes(self, user, **kwargs):
        """
        Check user attributes using the defined 'check_func'.

        Args:
            user (User): The user whose attributes are being checked.
            kwargs (Dict): The keyword arguments passed to the view.

        Returns:
            bool: True if the user attributes pass the check, otherwise False.
        """
        check_func = self.get_check_func()
        check_func = staticmethod(check_func)

        return check_func(user, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """
        Overrides the dispatch method to check user attributes using 'check_attributes'.
        If the attributes do not pass the check, it calls handle_no_permission.
        If they do, it proceeds with the view execution.
        """
        if not self.check_attributes(request.user, **kwargs):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
