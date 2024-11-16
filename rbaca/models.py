from datetime import timedelta

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Permission, UserManager
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.itercompat import is_iterable
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class RoleManager(models.Manager):
    """
    Custom manager for the Role model. Provides methods for managing roles.
    """

    def add_role(self, name: str):
        """
        Create and add a new role to the database.

        Args:
            name (str): The name of the role to add.

        Returns:
            Role: The role object created and added.
        """
        return self.create(name=name)

    def delete_role(self, role):
        """
        Delete a role from the database.

        Args:
            role (Role): The role to delete. Can be a role object or a role name (str).
        """
        if isinstance(role, str):
            role = self.filter(name=role).first()

        role.delete()

    @staticmethod
    def check_role_compatibility(roles, check_junior=True, check_incompatible=True):
        """
        Check compatibility of a set of roles.

        Args:
            roles (list of Role): A list of roles to check for compatibility.
            check_junior (bool): Decides if the function should check junior role compatibility.
            check_incompatible (bool): Decides if the function should check incompatible role compatibility.

        Returns:
            bool: True if roles are compatible, False otherwise.
        """
        if check_junior:
            junior_roles = Role.objects.filter(senior_role__in=roles)

            if not all(junior_role in roles for junior_role in junior_roles):
                return False
        if check_incompatible:
            for role in roles:
                if (
                    role.incompatible_roles
                    and role.incompatible_roles.all().intersection(roles)
                ):
                    return False
        return True


class Role(models.Model):
    """
    Model representing roles in the system.

    Fields:
        name (str): The name of the role.
        permissions (ManyToManyField): The permissions associated with the role.
        senior_role (ForeignKey): The senior role that this role reports to.
        incompatible_roles (ManyToManyField): Roles that are incompatible with this role.
    """

    name = models.CharField(max_length=255, null=True, blank=False, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    senior_role = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    incompatible_roles = models.ManyToManyField("self", blank=True)

    objects = models.Manager()
    manage = RoleManager()

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        permissions = [
            ("assign_role", "Can assign a role to another user"),
        ]

    def grant_perms(self, perms):
        """
        Grant permissions to the role.

        Args:
            perms (Permission or list of Permission): The permissions to be granted.
        Raises:
            ValueError: If permissions are not iterable and type of string.
        """
        if isinstance(perms, str):
            raise ValueError("perms must be instance of Permission")

        if not is_iterable(perms):
            perms = {perms}

        self.permissions.add(*perms)
        self.save()

    def revoke_perms(self, perms):
        """
        Revoke permissions from the role.

        Args:
            perms (Permission or list of Permission): The permissions to revoke.
        """
        if isinstance(perms, str):
            raise ValueError("perms must be instance of Permission")

        if not is_iterable(perms):
            perms = {perms}

        self.permissions.remove(*perms)
        self.save()

    def role_perms(self):
        """
        Get the permissions associated with the role.

        Returns:
            QuerySet[Role]: QuerySet of permissions for the role.
        """
        return self.permissions.all()

    def set_senior_role(self, senior_role):
        """
        Set the senior role for this role.

        Args:
            senior_role (Role): The senior role to be set.
        Raises:
            ValueError: If given senior role is an incompatible role of the junior role.
        """
        if self.incompatible_roles and senior_role in self.incompatible_roles.all():
            raise ValueError("an incompatible role can not be a senior role.")

        self.senior_role = senior_role
        self.incompatible_roles.add(*senior_role.incompatible_roles.all())
        self.save()

    def set_incompatible_roles(self, incompatible_roles):
        """
        Set the roles that are incompatible with this role.

        Args:
            incompatible_roles (list of Role): The roles that are incompatible with this role.
        Raises:
            ValueError: If given role is senior role.
        """
        if not is_iterable(incompatible_roles):
            incompatible_roles = {incompatible_roles}

        if self.senior_role and self.senior_role in incompatible_roles:
            raise ValueError("an senior role can not be in the incompatible roles.")

        self.incompatible_roles.set(incompatible_roles)

    def assigned_users(self):
        """
        Get all users with the given role.

        Returns:
            QuerySet[User]: QuerySet of users with the role.
        """
        return get_user_model().objects.filter(roles=self)

    def get_all_senior_roles(self):
        """
        Get all senior roles associated with this role.

        Returns:
            QuerySet[Role]: QuerySet of senior roles.
        """
        senior_roles = set()

        def collect_senior_roles(role):
            if role.senior_role:
                senior_roles.add(role.senior_role)
                collect_senior_roles(role.senior_role)

        collect_senior_roles(self)
        return Role.objects.filter(id__in=[role.id for role in senior_roles])

    def get_all_junior_roles(self):
        all_junior_roles = set()

        def collect_junior_roles(role):
            junior_roles = Role.objects.filter(senior_role=role)
            if junior_roles:
                for junior_role in junior_roles:
                    all_junior_roles.add(junior_role)
                    collect_junior_roles(junior_role)

        collect_junior_roles(self)
        return all_junior_roles

    def __str__(self) -> str:
        """
        Return the name of the role.

        Returns:
            str: The name of the role.
        """
        return self.name


class SessionManager(models.Manager):
    """
    Custom manager for the Session model. Provides methods for managing user sessions.
    """

    def add_session(self, user, active_roles=None):
        """
        Create and add a new session to the database.

        Args:
            user (User): The user associated with the session.
            active_roles (List[Role], optional): Active roles for the session. Default is None.

        Returns:
            Session: The session object created and added.
        """
        if active_roles is not None and not is_iterable(active_roles):
            active_roles = {active_roles}

        session = self.create(user=user)

        if active_roles:
            session.active_roles.set(active_roles)
            session.save()

        return session

    def delete_session(self, session):
        """
        Delete a session from the database.

        Args:
            session (Session): The session to delete.
        """
        session.delete()


class Session(models.Model):
    """
    Model representing user sessions in the system.

    Fields:
        user (User): The user associated with the session.
        active_roles (ManyToManyField): Active roles for the session.
        date_start (DateTimeField): The start date and time of the session.
        date_end (DateTimeField): The end date and time of the session.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=False, blank=False, on_delete=models.CASCADE
    )
    active_roles = models.ManyToManyField(Role, blank=False)
    date_start = models.DateTimeField(auto_now_add=True)
    date_end = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    manage = SessionManager()

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

    def add_active_roles(self, roles):
        """
        Add active roles to the session.

        Args:
            roles (Union[Role, List[Role]]): The active roles to be added.
        Raises:
            ValueError: If roles are not instances of role.
        """
        if isinstance(roles, str):
            raise ValueError("roles must be instance of Role.")

        if not is_iterable(roles):
            roles = {roles}

        self.active_roles.add(*roles)
        self.save()

    def drop_active_roles(self, roles):
        """
        Drop active roles from the session.

        Args:
            roles (Union[Role, List[Role]]): The active roles to be removed.
        """
        if not is_iterable(roles):
            roles = {roles}

        self.active_roles.remove(*roles)
        self.save()

    def session_roles(self):
        """
        Get the roles associated with the session.

        Returns:
            QuerySet[Role]: QuerySet of roles for the session.
        """

        return self.active_roles.all()

    def session_perms(self):
        """
        Get the permissions associated with the session.

        Returns:
            QuerySet[Permission]: QuerySet of permissions for the session.
        """
        session_roles_field = Session._meta.get_field("active_roles")
        session_roles_query = "role__%s" % session_roles_field.related_query_name()
        return Permission.objects.filter(**{session_roles_query: self})

    def close(self):
        """
        Close the session by setting the end date and time.
        """
        self.date_end = now()
        self.save()

    def __str__(self) -> str:
        """
        Return a string representation of the session.

        Returns:
            str: A string containing user, start date, and end date.
        """
        return str(self.user) + " " + str(self.date_start) + "-" + str(self.date_end)


class RoleExpirationManager(models.Manager):
    """
    Custom manager for the RoleExpiration model. Provides methods for managing role expirations.
    """

    def add_role_expiration(self, user, role, expiration_date):
        """
        Create and add a new role expiration to the database.

        Args:
            user (User): The user associated with the role expiration.
            role (Union[Role, str]): The role or role name to be expired.
            expiration_date (date): The date of role expiration.

        Returns:
            RoleExpiration: The role expiration object created and added.
        """
        if isinstance(role, str):
            role = Role.objects.filter(name=role).first()

        role_expiration = self.create(
            user=user, role=role, expiration_date=expiration_date
        )

        return role_expiration

    def get_expired_roles(self):
        """
        Get expired role expirations.

        Returns:
            QuerySet[RoleExpiration]: QuerySet of expired role expirations.
        """
        expired_roles = self.filter(expiration_date__lt=now())
        return expired_roles

    def remove_expired_roles(self):
        """
        Remove expired roles from users.
        """
        expired_roles = self.get_expired_roles()

        for expired_role in expired_roles:
            user = expired_role.user

            user.deassign_roles(expired_role.role)
            user.save()

        expired_roles.delete()


class RoleExpiration(models.Model):
    """
    Model representing role expirations in the system.

    Fields:
        expiration_date (date): The date of role expiration.
        user (User): The user associated with the role expiration.
        role (Role): The role to be expired.
    """

    expiration_date = models.DateField(null=False, blank=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=False, blank=False, on_delete=models.CASCADE
    )
    role = models.ForeignKey(Role, null=False, blank=False, on_delete=models.CASCADE)

    objects = models.Manager()
    manage = RoleExpirationManager()

    class Meta:
        verbose_name = _("Role expiration")
        verbose_name_plural = _("Role expirations")


class RoleMixin(models.Model):
    """
    Mixin class for user roles and permissions management.

    Fields:
        roles (ManyToManyField): The roles assigned to the user. Users inherit permissions from their roles.

    Usage:
        class CustomUser(User, RoleMixin):
            ...
    """

    roles = models.ManyToManyField(
        Role,
        verbose_name=_("roles"),
        blank=True,
        help_text=_(
            "The roles that are assigned to the user. A user will get all permissions "
            "granted to each of their roles."
        ),
        related_name="user_roles",
        related_query_name="user_role",
    )

    class Meta:
        abstract = True

    def assign_roles(self, roles):
        """
        Assign one or more roles to the user.

        Args:
            roles (Union[Role, List[Role]]): The role(s) to assign to the user.

        Raises:
            ValueError: If roles are not iterable or contain incompatible roles.

        Example:
            custom_user.assign_roles([Role1, Role2])
        """
        if isinstance(roles, str):
            raise ValueError("roles must be an (iterable) instance(s) of Role.")

        if not is_iterable(roles):
            roles = {roles}

        user_roles = self.roles.all()
        incompatible_roles = user_roles.values_list("incompatible_roles", flat=True)
        junior_roles = Role.objects.filter(senior_role__in=roles)

        for role in roles:
            if role.id in incompatible_roles:
                raise ValueError(
                    "role '%s' is incompatible with '%s'"
                    % (
                        role.name,
                        ", ".join(
                            role.incompatible_roles.all().values_list("name", flat=True)
                        ),
                    )
                )
        if not all(role in roles or role in user_roles for role in junior_roles):
            raise ValueError(
                "user '%s' needs all junior roles before assigning." % (self.username)
            )

        self.roles.add(*roles)
        self.save()

    def deassign_roles(self, roles):
        """
        Deassign one or more roles from the user.

        Args:
            roles (Union[Role, List[Role]]): The role(s) to deassign from the user.
        Raises:
            ValueError: If roles are not iterable and type of string.
        Example:
            custom_user.deassign_roles([Role1, Role2])
        """
        if isinstance(roles, str):
            raise ValueError("roles must be (iterable) instace(s) of Role")

        if not is_iterable(roles):
            roles = {roles}

        roles_to_deassign = []

        for role in roles:
            roles_to_deassign.extend(_user_get_senior_role(role))

        self.roles.remove(*roles_to_deassign)
        self.save()

    def assigned_roles(self):
        """
        Get the roles currently assigned to the user.

        Returns:
            QuerySet[Role]: QuerySet of roles assigned to the user.

        Example:
            assigned_roles = custom_user.assigned_roles()
        """
        return self.roles.all()

    def has_active_session(self, session_id=None):
        """
        Check if the user has an active session.

        Args:
            session_id (int, optional): ID of the session to check. Defaults to None.

        Returns:
            bool: True if the user has an active session, otherwise False.

        Example:
            has_active = custom_user.has_active_session(123)
        """
        return self.get_active_session(session_id) is not None

    def get_active_session(self, session_id=None):
        """
        Get the active session of the user.

        Args:
            session_id (int, optional): ID of the session to retrieve. Defaults to None.

        Returns:
            Session: The active session or None if no active session is found.

        Example:
            active_session = custom_user.get_active_session(123)
        """
        if not hasattr(self, "_session_cache"):
            self._session_cache = {}

        if session_id not in self._session_cache:
            session_qs = Session.objects.filter(user=self, date_end__isnull=True)

            if session_id:
                session_qs = session_qs.filter(id=session_id)

            session = session_qs.first()

            if session:
                if session.date_start < now() - timedelta(
                    seconds=settings.SESSION_TIMEOUT_ABSOLUTE
                ):
                    session.date_end = now()
                    session.save()
                    session = None

            self._session_cache[session_id] = session
        return self._session_cache[session_id]

    def has_role(self, role):
        """
        Check if the user has a specific role.

        Args:
            role (Union[Role, str]): The role or role name to check.

        Returns:
            bool: True if the user has the specified role, otherwise False.

        Example:
            has_role = custom_user.has_role('Role1')
        """
        if self.is_active and self.is_superuser:
            return True

        if not isinstance(role, str):
            role = role.name

        return _user_has_role(self, role)

    def get_roles_permissions(self, obj=None):
        """
        Get permissions associated with the user's roles.

        Args:
            obj (object, optional): The object to check permissions for. Defaults to None.

        Returns:
            QuerySet[Permission]: QuerySet of permissions associated with the user's roles.
        """

        return _user_get_permissions(self, obj, "role")

    def get_all_permissions(self, obj=None):
        """
        Get all permissions associated with the user, including those inherited from roles.

        Args:
            obj (object, optional): The object to check permissions for. Defaults to None.

        Returns:
            QuerySet[Permission]: QuerySet of all permissions associated with the user.
        """
        return _user_get_permissions(self, obj, "all")

    def has_perm(self, perm, obj=None):
        """
        Check if the user has a specific permission.

        Args:
            perm (str): The permission to check.

        Returns:
            bool: True if the user has the specified permission, otherwise False.

        Example:
            has_permission = custom_user.has_perm('myapp.can_do_something')
        """
        if self.is_active and self.is_superuser:
            return True

        return _user_has_perm(self, perm, obj)

    def has_perms(self, permission_list, obj=None):
        """
        Check if the user has a list of specific permissions.

        Args:
            permission_list (Union[str, List[str], Permission]): The list of permissions to check.

        Returns:
            bool: True if the user has all specified permissions, otherwise False.

        Example:
            permission_list = ['myapp.can_do_this', 'myapp.can_do_that']
            has_permissions = custom_user.has_perms(permission_list)
        """
        if not is_iterable(permission_list) or isinstance(permission_list, str):
            raise ValueError("perm_list must be an iterable of permissions")

        return all(self.has_perm(perm, obj) for perm in permission_list)

    def has_module_perms(self, app_label):
        """
        Check if the user has permissions for a specific app/module.

        Args:
            app_label (str): The label of the app/module.

        Returns:
            bool: True if the user has permissions for the specified app/module, otherwise False.

        Example:
            has_permissions = custom_user.has_module_perms('myapp')
        """
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)


def _user_get_senior_role(role):
    """
    Recursively retrieve the senior role of a given role.

    Args:
        role (Role or List[Role]): The role(s) to retrieve the senior role for.

    Returns:
        Role or List[Role]: The senior role or list of senior roles, or None if no senior role is found.
    """
    if not is_iterable(role):
        role = [role]

    if role[-1].senior_role is not None:
        role.append(role[-1].senior_role)
        return _user_get_senior_role(role)

    else:
        return role


def _user_has_role(user, role):
    """
    Check if the user has a specific role using authentication backends.

    Args:
        user (User): The user to check for the role.
        role (str or Role): The role or role name to check.

    Returns:
        bool: True if the user has the specified role, otherwise False.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_role"):
            continue
        try:
            if backend.has_role(user, role):
                return True
        except PermissionDenied:
            return False

    return False


def _user_get_permissions(user, obj, from_name):
    """
    Retrieve permissions associated with the user's roles using authentication backends.

    Args:
        user (User): The user to retrieve permissions for.
        obj (object): The object to check permissions for, or None.
        from_name (str): The source of permissions to retrieve (e.g., 'role' or 'all').

    Returns:
        set: A set of permissions associated with the user.
    """
    permissions = set()
    name = "get_%s_permissions" % from_name

    for backend in auth.get_backends():
        if hasattr(backend, name):
            permissions.update(getattr(backend, name)(user, obj))

    return permissions


def _user_has_perm(user, perm, obj):
    """
    Check if the user has a specific permission using authentication backends.

    Args:
        user (User): The user to check for the permission.
        perm (str): The permission to check.
        obj (object): The object to check permissions for, or None.

    Returns:
        bool: True if the user has the specified permission, otherwise False.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_perm"):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False

    return False


def _user_has_module_perms(user, app_label):
    """
    Check if the user has permissions for a specific app/module using authentication backends.

    Args:
        user (User): The user to check for permissions.
        app_label (str): The label of the app/module.

    Returns:
        bool: True if the user has permissions for the specified app/module, otherwise False.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_module_perms"):
            continue
        try:
            if backend.has_module_perms(user, app_label):
                return True
        except PermissionDenied:
            return False

    return False


class AbstractRoleUser(AbstractBaseUser, RoleMixin):
    """
    An abstract user class with role-based permissions.

    This class provides a customizable user model with role-based permissions and other common user fields.

    Attributes:
        username (str): A unique username for the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        email (str): The email address of the user.
        is_superuser (bool): A boolean indicating whether the user has superuser status.
        is_staff (bool): A boolean indicating whether the user can log into the admin site.
        is_active (bool): A boolean indicating whether the user should be treated as active.
        date_joined (datetime): The date and time when the user joined.
        objects (UserManager): The manager for handling user objects.
        EMAIL_FIELD (str): The field used as the unique identifier for the user (email in this case).
        USERNAME_FIELD (str): The field used as the username for the user (username in this case).
        REQUIRED_FIELDS (List[str]): A list of required fields for creating a user.
    """

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = True

    def clean(self):
        """
        Clean method for normalizing email.

        This method ensures that the email is properly formatted.
        """
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Retrieve the user's full name.

        Returns:
            str: The full name of the user.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """
        Retrieve the user's short name.

        Returns:
            str: The short name of the user.
        """
        return self.first_name


class User(AbstractRoleUser):
    """
    A concrete implementation of the AbstractRoleUser class.

    This class provides a concrete implementation of the abstract user with role-based permissions.
    """

    roles = models.ManyToManyField(
        Role,
        verbose_name=_("roles"),
        blank=True,
        help_text=_(
            "The roles that are assigned to the user. A user will get all permissions "
            "granted to each of their roles."
        ),
        related_name="roles",
        related_query_name="role",
    )
