from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from rbaca.models import Role, Session, User
from rbaca.templatetags.rbaca_tags import has_active_session, has_perm, has_role


class TestTemplateTags(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        content_type = ContentType.objects.get_for_model(Role)

        self.perm = Permission.objects.create(
            name="test_role", content_type=content_type, codename="test_role"
        )
        self.session_perm = Permission.objects.create(
            name="test_session", content_type=content_type, codename="test_session"
        )
        self.role = Role.objects.create(name="test_role")
        self.role.permissions.add(*{self.perm})
        self.user.roles.add(*{self.role})
        self.user.save()

        self.session_role = Role.objects.create(name="test_session")
        self.session_role.permissions.add(*{self.session_perm})
        self.user.roles.add(*{self.session_role})
        self.user.save()

        self.session = Session.objects.create(user=self.user)
        self.session.active_roles.add(*{self.session_role})
        self.session.save()

    def test_has_perm(self):
        self.assertTrue(has_perm(self.user, "rbaca.test_role"))
        self.assertFalse(has_perm(self.user, "rbaca.test"))

    def test_has_perm_superuser(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(has_perm(self.user, "rbaca.test_role"))
        self.assertTrue(has_perm(self.user, "rbaca.test"))

    @override_settings(USE_SESSIONS=True)
    def test_has_perm_session_based(self):
        self.assertTrue(has_perm(self.user, "rbaca.test_session"))
        self.assertFalse(has_perm(self.user, "rbaca.test_role"))

    @override_settings(USE_SESSIONS=True)
    def test_has_perm_superuser_session_based(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(has_perm(self.user, "rbaca.test_session"))
        self.assertTrue(has_perm(self.user, "rbaca.test_role"))

    def test_has_role(self):
        self.assertTrue(has_role(self.user, "test_role"))
        self.assertFalse(has_role(self.user, "test_role2"))

    def test_has_role_superuser(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(has_role(self.user, "test_role"))
        self.assertTrue(has_role(self.user, "test_role2"))

    @override_settings(USE_SESSIONS=True)
    def test_has_role_session_based(self):
        self.assertTrue(has_role(self.user, "test_session"))
        self.assertFalse(has_role(self.user, "test_role"))

    @override_settings(USE_SESSIONS=True)
    def test_has_role_superuser_session_based(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(has_role(self.user, "test_session"))
        self.assertTrue(has_role(self.user, "test_role"))

    @override_settings(USE_SESSIONS=True)
    def test_has_active_session(self):
        self.assertTrue(has_active_session(self.user))

    @override_settings(USE_SESSIONS=True)
    def test_has_active_session_superuser(self):
        self.session.delete()
        self.assertFalse(has_active_session(self.user))
