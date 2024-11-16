from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission

from rbaca.models import Role, Session

UserModel = get_user_model()


class RoleBackend(BaseBackend):
    """
    Custom authentication backend for handling user roles and permissions.

    This backend extends Django's authentication system to provide role-based access control.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user based on the provided username and password.

        Args:
            request (HttpRequest): The current request object.
            username (str): The username of the user.
            password (str, hashed): The user's password.

        Returns:
            Union[User, None]: The authenticated user if successful, otherwise None.
        """
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def user_can_authenticate(self, user):
        """
        Check if a user is active and can be authenticated.

        Args:
            user (User): The user to check.

        Returns:
            bool: True if the user is active, False if the user is inactive.
        """
        is_active = getattr(user, "is_active", None)
        return is_active or is_active is None

    def _get_roles_permissions(self, user_obj):
        """
        Get the permissions associated with the user's roles.

        Args:
            user_obj (User): The user for which permissions are retrieved.

        Returns:
            QuerySet[Permission]: A set of permissions associated with the user's roles.
        """
        if getattr(settings, "USE_SESSIONS", False):
            session = user_obj.get_active_session()
            if session:
                session_roles_field = Session._meta.get_field("active_roles")
                session_roles_query = (
                    "role__%s" % session_roles_field.related_query_name()
                )
                permissions = Permission.objects.filter(
                    **{session_roles_query: session}
                )
            else:
                permissions = Permission.objects.none()
        else:
            user_roles_field = get_user_model()._meta.get_field("roles")
            user_roles_query = "role__%s" % user_roles_field.related_query_name()
            permissions = Permission.objects.filter(**{user_roles_query: user_obj})
        return permissions

    def _get_user_roles(self, user_obj):
        """
        Get the roles associated with the user.

        Args:
            user_obj (User): The user for which roles are retrieved.

        Returns:
            QuerySet[Role]: A set of roles associated with the user.
        """
        if getattr(settings, "USE_SESSIONS", False):
            session = user_obj.get_active_session()

            if session:
                roles = session.active_roles.all()
            else:
                roles = Role.objects.none()
        else:
            roles = user_obj.roles.all()

        return roles

    def _get_permissions(self, user_obj, obj):
        """
        Get permissions for the user based on roles.

        Args:
            user_obj (User): The user for which permissions are retrieved.
            obj (Object): The object for which permissions are checked.

        Returns:
            QuerySet[Permission]: A set of permissions granted to the user.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        perm_cache_name = "_%s_perm_cache" % "roles"

        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                perms = getattr(self, "_get_%s_permissions" % "roles")(user_obj)
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(
                user_obj,
                perm_cache_name,
                {f"{ct}.{name}" for ct, name in perms},
            )
        return getattr(user_obj, perm_cache_name)

    def _get_roles(self, user_obj, obj):
        """
        Get roles for the user based on roles.

        Args:
            user_obj (User): The user for which roles are retrieved.
            obj (Object): The object for which roles are checked.

        Returns:
            Set[Role]: A set of roles granted to the user.
        """

        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        roles_cache_name = "_%s_cache" % "roles"

        if not hasattr(user_obj, roles_cache_name):
            if user_obj.is_superuser:
                roles = Role.objects.all()
            else:
                roles = getattr(self, "_get_%s_roles" % "user")(user_obj)
            roles = roles.values_list("name").order_by()
            setattr(user_obj, roles_cache_name, {"%s" % (name) for name in roles})
        return getattr(user_obj, roles_cache_name)

    def get_user_permissions(self, user_obj, obj=None):
        """
        Get the permissions granted to the user.

        Args:
            user_obj (User): The user for which permissions are retrieved.
            obj (Object): The object for which permissions are checked.

        Returns:
            QuerySet[Permission]: A set of permissions granted to the user.
        """
        return self._get_permissions(user_obj, obj)

    def get_role_permissions(self, user_obj, obj=None):
        """
        Get the permissions granted to the user based on roles.

        Args:
            user_obj (User): The user for which permissions are retrieved.
            obj (Object): The object for which permissions are checked.

        Returns:
            QuerySet[Permission]: A set of permissions granted to the user based on roles.
        """
        return self._get_permissions(user_obj, obj)

    def get_user_roles(self, user_obj, obj=None):
        """
        Get the roles granted to the user.

        Args:
            user_obj (User): The user for which roles are retrieved.
            obj (Object): The object for which roles are checked.

        Returns:
            QuerySet[Role]: A set of roles granted to the user.
        """
        return self._get_roles(user_obj, obj)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Get all permissions granted to the user.

        Args:
            user_obj (User): The user for which permissions are retrieved.
            obj (Object): The object for which permissions are checked.

        Returns:
            QuerySet[Permission]: A set of all permissions granted to the user.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, "_roles_perm_cache"):
            user_obj._perm_cache = super().get_all_permissions(user_obj)
        return user_obj._perm_cache

    def has_role(self, user_obj, role):
        """
        Check if the user has a specific role.

        Args:
            user_obj (User): The user to check.
            role (Union[Role, str]): The role to verify.

        Returns:
            bool: True if the user has the specified role, otherwise False.
        """
        return role in self.get_user_roles(user_obj)

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if the user has a specific permission.

        Args:
            user_obj (User): The user to check.
            perm (Permission): The permission to verify.
            obj (Object): The object for which the permission is checked.

        Returns:
            bool: True if the user has the specified permission, otherwise False.
        """
        return user_obj.is_active and super().has_perm(user_obj, perm, obj=obj)

    def has_module_perms(self, user_obj, app_label):
        """
        Check if the user has permissions for a specific app (module).

        Args:
            user_obj (User): The user to check.
            app_label (str): The app (module) label to verify.

        Returns:
            bool: True if the user has permissions for the specified app, otherwise False.
        """
        return user_obj.is_active and any(
            perm[: perm.index(".")] == app_label
            for perm in self.get_all_permissions(user_obj)
        )

    def get_user(self, user_id):
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            Union[User, None]: The user with the provided ID if found, otherwise None.
        """
        try:
            user = UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def get_node_access(self, user_obj):
        """
        Get access to specific nodes based on user roles.

        Args:
            user_obj (User): The user for which node access is checked.

        Returns:
            List[str]: A list of nodes that the user has access to based on their roles.
        """
        if hasattr(settings, "NODE_ACCESS"):
            roles = self._get_user_roles(user_obj).values_list("name", flat=True)
            node_access = []

            if user_obj.is_superuser:
                return list(settings.NODE_ACCESS.keys())

            for node in settings.NODE_ACCESS:
                if any(item in roles for item in settings.NODE_ACCESS[node]):
                    node_access.append(node)
            return node_access
        else:
            return []
