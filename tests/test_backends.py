from unittest import mock

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import MD5PasswordHasher
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, modify_settings, override_settings

from rbaca.backends import RoleBackend
from rbaca.models import Role, Session, User


class CountingMD5PasswordHasher(MD5PasswordHasher):
    """Hasher that counts how many times it computes a hash. Adopted from Django"""

    calls = 0

    def encode(self, *args, **kwargs):
        type(self).calls += 1
        return super().encode(*args, **kwargs)


class TestRoleBackendRoleBased(TestCase):
    backend = "rbaca.backends.RoleBackend"
    UserModel = User
    user_credentials = {"username": "test", "password": "test"}

    def create_users(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.superuser = User.objects.create_superuser(
            username="test2",
            email="test2@example.com",
            password="test",
        )

    def test_authenticate_inactive(self):
        """
        An inactive user can't authenticate.
        """
        self.assertEqual(authenticate(**self.user_credentials), self.user)
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(**self.user_credentials))

    def setUp(self):
        self.patched_settings = modify_settings(
            AUTHENTICATION_BACKENDS={"append": self.backend},
        )
        self.patched_settings.enable()
        self.create_users()

    def tearDown(self):
        self.patched_settings.disable()
        ContentType.objects.clear_cache()

    def test_has_perm(self):
        backend = RoleBackend()
        Role.objects.create(name="test_role")

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertIs(user.has_perm("rbaca.test"), False)

        user.is_superuser = True
        user.save()
        self.assertIs(user.has_perm("rbaca.test"), True)
        self.assertEqual(backend._get_roles(user, None), {"test_role"})

        user.is_superuser = True
        user.is_active = False
        user.save()
        self.assertIs(user.has_perm("rbaca.test"), False)

    def test_custom_perms(self):
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        expected_user_perms = {"rbaca.test_role"}

        perm = Permission.objects.create(
            name="test_role", content_type=content_type, codename="test_role"
        )
        role = Role.objects.create(name="test_role")
        role.permissions.add(perm)
        user.roles.add(role)
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertEqual(
            user.get_all_permissions(), {*expected_user_perms, "rbaca.test_role"}
        )
        self.assertEqual(user.get_roles_permissions(), expected_user_perms)

        user = AnonymousUser()
        self.assertIs(user.has_perm("test_role"), False)

    def test_has_no_object_perm(self):
        """Regressiontest for #12462"""
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        perm = Permission.objects.create(
            name="test_role", content_type=content_type, codename="test_role"
        )
        role = Role.objects.create(name="test_role")
        role.permissions.add(perm)
        user.roles.add(role)

        self.assertIs(user.has_perm("rbaca.test_role", "object"), False)
        self.assertEqual(user.get_all_permissions("object"), set())
        self.assertIs(user.has_perm("rbaca.test_role"), True)
        self.assertEqual(user.get_all_permissions(), {"rbaca.test_role"})

    def test_anonymous_has_no_permissions(self):
        backend = RoleBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        role_perm = Permission.objects.create(
            name="test2", content_type=content_type, codename="test_role"
        )

        role = Role.objects.create(name="test_role")
        user.roles.add(role)
        role.permissions.add(role_perm)

        self.assertEqual(backend.get_all_permissions(user), {"rbaca.test_role"})
        self.assertEqual(backend.get_role_permissions(user), {"rbaca.test_role"})

        with mock.patch.object(self.UserModel, "is_anonymous", True):
            self.assertEqual(backend.get_all_permissions(user), set())
            self.assertEqual(backend.get_role_permissions(user), set())

    def test_inactive_has_no_permissions(self):
        backend = RoleBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        role_perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test_role"
        )

        role = Role.objects.create(name="test_role")
        user.roles.add(role)
        role.permissions.add(role_perm)

        self.assertEqual(backend.get_all_permissions(user), {"rbaca.test_role"})
        self.assertEqual(backend.get_role_permissions(user), {"rbaca.test_role"})

        user.is_active = False
        user.save()

        self.assertEqual(backend.get_all_permissions(user), set())
        self.assertEqual(backend.get_role_permissions(user), set())
        self.assertEqual(backend._get_roles(user, None), set())

    def test_get_all_superuser_permissions(self):
        user = self.UserModel._default_manager.get(pk=self.superuser.pk)
        self.assertEqual(len(user.get_all_permissions()), len(Permission.objects.all()))

    @override_settings(
        PASSWORD_HASHERS=["tests.test_backends.CountingMD5PasswordHasher"]
    )
    def test_authentication_timing(self):
        self.user.set_password("test")
        self.user.save()

        CountingMD5PasswordHasher.calls = 0
        username = getattr(self.user, self.UserModel.USERNAME_FIELD)
        authenticate(username=username, password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

        CountingMD5PasswordHasher.calls = 0
        authenticate(username="no_such_user", password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

    @override_settings(
        PASSWORD_HASHERS=["auth_tests.test_auth_backends.CountingMD5PasswordHasher"]
    )
    def test_authentication_without_credentials(self):
        CountingMD5PasswordHasher.calls = 0
        for credentials in (
            {},
            {"username": getattr(self.user, self.UserModel.USERNAME_FIELD)},
            {"password": "test"},
        ):
            with self.subTest(credentials=credentials):
                with self.assertNumQueries(0):
                    authenticate(**credentials)
                self.assertEqual(CountingMD5PasswordHasher.calls, 0)

    def test_get_user(self):
        backend = RoleBackend()
        self.assertEqual(backend.get_user(self.user.id), self.user)
        self.assertEqual(None, backend.get_user(-1))


@override_settings(USE_SESSIONS=True)
class TestRoleBackendSessionBased(TestCase):
    backend = "rbaca.backends.RoleBackend"
    UserModel = User
    user_credentials = {"username": "test", "password": "test"}

    def create_users(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.superuser = User.objects.create_superuser(
            username="test2",
            email="test2@example.com",
            password="test",
        )

    def test_authenticate_inactive(self):
        """
        An inactive user can't authenticate.
        """
        self.assertEqual(authenticate(**self.user_credentials), self.user)
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(authenticate(**self.user_credentials))

    def setUp(self):
        self.patched_settings = modify_settings(
            AUTHENTICATION_BACKENDS={"append": self.backend},
        )
        self.patched_settings.enable()
        self.create_users()

    def tearDown(self):
        self.patched_settings.disable()
        ContentType.objects.clear_cache()

    def test_has_perm(self):
        backend = RoleBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertIs(user.has_perm("rbaca.test"), False)
        self.assertFalse(backend._get_roles_permissions(user))
        self.assertFalse(backend._get_user_roles(user))

        user.is_superuser = True
        user.save()
        self.assertIs(user.has_perm("rbaca.test"), True)

        user.is_superuser = True
        user.is_active = False
        user.save()
        self.assertIs(user.has_perm("rbaca.test"), False)

    def test_custom_perms(self):
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        expected_user_perms = {"rbaca.test_role"}

        perm = Permission.objects.create(
            name="test_role", content_type=content_type, codename="test_role"
        )
        role = Role.objects.create(name="test_role")
        role.permissions.add(perm)

        user.roles.add(role)
        session = Session.objects.create(user=user)
        session.active_roles.add(role)

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertEqual(
            user.get_all_permissions(), {*expected_user_perms, "rbaca.test_role"}
        )
        self.assertEqual(user.get_roles_permissions(), expected_user_perms)

        user = AnonymousUser()
        self.assertIs(user.has_perm("test_role"), False)

    def test_has_no_object_perm(self):
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        perm = Permission.objects.create(
            name="test_role", content_type=content_type, codename="test_role"
        )
        role = Role.objects.create(name="test_role")
        role.permissions.add(perm)
        user.roles.add(role)

        session = Session.objects.create(user=user)
        session.active_roles.add(role)

        self.assertIs(user.has_perm("rbaca.test_role", "object"), False)
        self.assertEqual(user.get_all_permissions("object"), set())
        self.assertIs(user.has_perm("rbaca.test_role"), True)
        self.assertEqual(user.get_all_permissions(), {"rbaca.test_role"})

    def test_anonymous_has_no_permissions(self):
        backend = RoleBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        role_perm = Permission.objects.create(
            name="test2", content_type=content_type, codename="test_role"
        )

        role = Role.objects.create(name="test_role")
        user.roles.add(role)
        role.permissions.add(role_perm)

        session = Session.objects.create(user=user)
        session.active_roles.add(role)

        self.assertEqual(backend.get_all_permissions(user), {"rbaca.test_role"})
        self.assertEqual(backend.get_role_permissions(user), {"rbaca.test_role"})

        with mock.patch.object(self.UserModel, "is_anonymous", True):
            self.assertEqual(backend.get_all_permissions(user), set())
            self.assertEqual(backend.get_role_permissions(user), set())

    def test_inactive_has_no_permissions(self):
        backend = RoleBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Role)
        role_perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test_role"
        )

        role = Role.objects.create(name="test_role")
        user.roles.add(role)
        role.permissions.add(role_perm)

        session = Session.objects.create(user=user)
        session.active_roles.add(role)

        self.assertEqual(backend.get_all_permissions(user), {"rbaca.test_role"})
        self.assertEqual(backend.get_role_permissions(user), {"rbaca.test_role"})

        user.is_active = False
        user.save()

        self.assertEqual(backend.get_all_permissions(user), set())
        self.assertEqual(backend.get_role_permissions(user), set())

    def test_get_all_superuser_permissions(self):
        user = self.UserModel._default_manager.get(pk=self.superuser.pk)
        self.assertEqual(len(user.get_all_permissions()), len(Permission.objects.all()))

    @override_settings(
        PASSWORD_HASHERS=["tests.test_backends.CountingMD5PasswordHasher"]
    )
    def test_authentication_timing(self):
        self.user.set_password("test")
        self.user.save()

        CountingMD5PasswordHasher.calls = 0
        username = getattr(self.user, self.UserModel.USERNAME_FIELD)
        authenticate(username=username, password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

        CountingMD5PasswordHasher.calls = 0
        authenticate(username="no_such_user", password="test")
        self.assertEqual(CountingMD5PasswordHasher.calls, 1)

    @override_settings(
        PASSWORD_HASHERS=["auth_tests.test_auth_backends.CountingMD5PasswordHasher"]
    )
    def test_authentication_without_credentials(self):
        CountingMD5PasswordHasher.calls = 0
        for credentials in (
            {},
            {"username": getattr(self.user, self.UserModel.USERNAME_FIELD)},
            {"password": "test"},
        ):
            with self.subTest(credentials=credentials):
                with self.assertNumQueries(0):
                    authenticate(**credentials)
                self.assertEqual(CountingMD5PasswordHasher.calls, 0)
