from datetime import datetime, timedelta
from uuid import UUID

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.utils.timezone import now

from rbaca.models import Role, RoleExpiration, Session, User


class TestRoleModel(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        User.objects.create(username="foo")

    def setUp(self) -> None:
        self.permissions = Permission.objects.filter(
            name__in=[
                "Can add role",
                "Can view role",
                "Can change role",
                "Can delete role",
            ]
        )
        self.user = User.objects.filter(username="foo").first()
        self.senior_role = Role.objects.create(name="senior")
        self.junior_role = Role.objects.create(
            name="junior", senior_role=self.senior_role
        )
        self.incompatible_role = Role.objects.create(name="beaver")
        self.incompatible_role.incompatible_roles.set(
            [self.junior_role, self.senior_role]
        )

    def test_role_manager_add_role(self):
        role = Role.manage.add_role(name="bar")
        self.assertEqual(role.name, "bar")

    def test_role_manager_delete_role(self):
        Role.manage.delete_role(self.senior_role)
        self.assertFalse(Role.objects.filter(name="senior"))

    def test_role_manager_delete_role_by_name(self):
        Role.manage.delete_role(self.senior_role.name)
        self.assertFalse(Role.objects.filter(name="senior"))

    def test_role_assigned_users(self):
        self.user2 = User.objects.create(username="bar")
        self.user.roles.set([self.senior_role, self.junior_role])
        self.user2.roles.set([self.junior_role])
        self.user.save()
        self.user2.save()

        assigned_users = Role.assigned_users(self.junior_role)
        self.assertEqual(len(assigned_users), 2)
        self.assertTrue(self.user in assigned_users)
        self.assertTrue(self.user2 in assigned_users)

        assigned_users = Role.assigned_users(self.senior_role)
        self.assertEqual(len(assigned_users), 1)
        self.assertTrue(self.user in assigned_users)

    def test_role_grant_perms(self):
        self.senior_role.grant_perms(self.permissions)
        self.senior_role.refresh_from_db()
        self.assertQuerysetEqual(self.senior_role.permissions.all(), self.permissions)

    def test_role_grant_perms_not_iterable(self):
        self.senior_role.grant_perms(self.permissions.first())
        self.senior_role.refresh_from_db()
        self.assertEqual(
            self.senior_role.permissions.all().first(), self.permissions.first()
        )

    def test_role_grant_perms_string(self):
        with self.assertRaises(ValueError):
            self.senior_role.grant_perms("rbaca.test")

    def test_role_revoke_perms(self):
        self.senior_role.grant_perms(self.permissions)
        self.senior_role.revoke_perms(self.permissions)
        self.senior_role.refresh_from_db()
        self.assertQuerysetEqual(
            self.senior_role.permissions.all(), Permission.objects.none()
        )

    def test_role_revoke_perms_not_iterable(self):
        self.senior_role.grant_perms(self.permissions.first())
        self.senior_role.refresh_from_db()
        self.senior_role.revoke_perms(self.permissions.first())
        self.senior_role.refresh_from_db()
        self.assertFalse(self.senior_role.permissions.all())

    def test_role_revoke_perms_string(self):
        with self.assertRaises(ValueError):
            self.senior_role.revoke_perms("rbaca.test")

    def test_role_role_perms(self):
        self.senior_role.grant_perms(self.permissions)
        role_perms = self.senior_role.role_perms()
        self.assertQuerysetEqual(role_perms, self.permissions)

    def test_role_set_senior_role(self):
        self.junior_role.senior_role = None
        self.junior_role.save()
        self.junior_role.set_senior_role(self.senior_role)
        self.junior_role.refresh_from_db()
        self.assertEqual(self.junior_role.senior_role, self.senior_role)

    def test_role_set_senior_role_with_incompatible_role(self):
        self.junior_role.senior_role = None
        self.senior_role.save()

        with self.assertRaises(ValueError):
            self.senior_role.set_senior_role(self.incompatible_role)

    def test_role_set_incompatible_roles(self):
        self.incompatible_role.incompatible_roles.clear()
        self.incompatible_role.save()
        self.incompatible_role.set_incompatible_roles(
            [self.senior_role, self.junior_role]
        )
        self.incompatible_role.refresh_from_db()
        incompatible_roles = self.incompatible_role.incompatible_roles.all()

        self.assertTrue(self.junior_role in incompatible_roles)
        self.assertTrue(self.senior_role in incompatible_roles)

    def test_role_set_incompatible_roles_not_iterable(self):
        self.incompatible_role.incompatible_roles.clear()
        self.incompatible_role.save()
        self.incompatible_role.set_incompatible_roles(self.senior_role)
        self.incompatible_role.refresh_from_db()
        incompatible_roles = self.incompatible_role.incompatible_roles.all()

        self.assertTrue(self.senior_role in incompatible_roles)

    def test_role_set_incompatible_roles_with_senior_role(self):
        with self.assertRaises(ValueError):
            self.junior_role.set_incompatible_roles([self.senior_role])

    def test_get_all_senior_roles(self):
        senior_roles = self.senior_role.get_all_senior_roles()
        self.assertEqual(set(senior_roles), set())

        senior_roles = self.junior_role.get_all_senior_roles()
        self.assertEqual(set(senior_roles), {self.senior_role})

    def test_role_to_str(self):
        self.assertEqual(str(self.junior_role), "junior")


class TestSessionModel(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        permissions = Permission.objects.filter(
            name__in=[
                "Can add role",
                "Can view role",
                "Can change role",
                "Can delete role",
            ]
        )

        User.objects.create(username="foo")
        role1 = Role.objects.create(name="1")
        role1.grant_perms(permissions[:2])
        role2 = Role.objects.create(name="2")
        role2.grant_perms(permissions[2:4])

    def setUp(self) -> None:
        self.permissions = Permission.objects.filter(
            name__in=[
                "Can add role",
                "Can view role",
                "Can change role",
                "Can delete role",
            ]
        )
        self.user = User.objects.filter(username="foo").first()
        self.role1 = Role.objects.all().first()
        self.role2 = Role.objects.all().last()

    def test_session_manager_add_session_without_roles(self):
        session = Session.manage.add_session(self.user)

        self.assertEqual(session.user, self.user)

    def test_session_manager_add_session(self):
        session = Session.manage.add_session(self.user, self.role1)
        active_roles = session.active_roles.all()

        self.assertEqual(session.user, self.user)
        self.assertTrue(self.role1 in active_roles)

    def test_session_manager_delete_session(self):
        session = Session.manage.add_session(self.user)
        Session.manage.delete_session(session)

        self.assertEqual(Session.objects.all().count(), 0)

    def test_session_add_active_roles(self):
        session = Session.manage.add_session(self.user)
        session.add_active_roles(self.role1)

        self.assertTrue(self.role1 in session.active_roles.all())

    def test_session_add_active_roles_string(self):
        session = Session.manage.add_session(self.user)

        with self.assertRaises(ValueError):
            session.add_active_roles(self.role1.name)

    def test_session_drop_active_roles(self):
        session = Session.manage.add_session(self.user, self.role1)
        session.drop_active_roles(self.role1)

        try:
            session.drop_active_roles(self.role2)
        except Exception:
            self.assertFalse(True)

        self.assertFalse(session.active_roles.all())

    def test_session_session_roles(self):
        session = Session.manage.add_session(self.user, [self.role1, self.role2])
        active_roles = session.session_roles()

        self.assertEqual(len(active_roles), 2)
        self.assertTrue(self.role1 in active_roles)
        self.assertTrue(self.role2 in active_roles)

    def test_session_session_perms(self):
        session = Session.manage.add_session(self.user, [self.role1, self.role2])
        session_perms = session.session_perms()

        self.assertQuerysetEqual(session_perms, self.permissions)

    def test_session_close(self):
        session = Session.objects.create(user=self.user)
        session.close()

        self.assertTrue(session.date_end is not None)

    def test_session_str(self):
        session = Session.objects.create(user=self.user)
        session.close()

        self.assertEqual(
            str(session),
            str(self.user)
            + " "
            + str(session.date_start)
            + "-"
            + str(session.date_end),
        )


class TestRoleExpirationModel(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        User.objects.create(username="foo")
        Role.objects.create(name="role")

    def setUp(self) -> None:
        self.user = User.objects.all().first()
        self.role = Role.objects.all().first()

    def test_role_expiration_manager_add_role_expiration(self):
        expiration_date = now()
        role_expiration = RoleExpiration.manage.add_role_expiration(
            self.user, self.role, expiration_date
        )

        self.assertEqual(role_expiration.user, self.user)
        self.assertEqual(role_expiration.role, self.role)
        self.assertEqual(role_expiration.expiration_date, expiration_date)

    def test_role_expiration_manager_add_role_expiration_with_string(self):
        expiration_date = now()
        role_expiration = RoleExpiration.manage.add_role_expiration(
            self.user, self.role.name, expiration_date
        )

        self.assertEqual(role_expiration.user, self.user)
        self.assertEqual(role_expiration.role, self.role)
        self.assertEqual(role_expiration.expiration_date, expiration_date)

    def test_role_expiration_manager_get_expired_roles(self):
        expiration_date = now()
        expired = RoleExpiration.manage.add_role_expiration(
            self.user, self.role, expiration_date - timedelta(days=1)
        )
        not_expired = RoleExpiration.manage.add_role_expiration(
            self.user, self.role, expiration_date + timedelta(days=1)
        )

        all_expired = RoleExpiration.manage.get_expired_roles()

        self.assertEqual(len(all_expired), 1)
        self.assertTrue(expired in all_expired)
        self.assertTrue(not_expired not in all_expired)

    def test_role_expiration_manager_remove_expired_roles(self):
        self.user.roles.add(*[self.role])
        self.user.save()
        expiration_date = now()
        RoleExpiration.manage.add_role_expiration(
            self.user, self.role, expiration_date - timedelta(days=1)
        )
        RoleExpiration.manage.remove_expired_roles()

        self.assertQuerysetEqual(self.user.roles.all(), Role.objects.none())

    def test_role_expiration_uuid_generation(self):
        expiration_date = now()
        role_expiration = RoleExpiration.manage.add_role_expiration(
            self.user, self.role.name, expiration_date
        )
        self.assertIsInstance(role_expiration.uuid, UUID)

    def test_role_expiration_get_by_uuid(self):
        expiration_date = now()
        role_expiration = RoleExpiration.manage.add_role_expiration(
            self.user, self.role.name, expiration_date
        )
        get_by_uuid = RoleExpiration.objects.get(uuid=role_expiration.uuid)
        self.assertEqual(get_by_uuid, role_expiration)


class TestRoleMixinModel(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        content_type = ContentType.objects.get_for_model(Role)
        role_perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test_role"
        )
        role_perm2 = Permission.objects.create(
            name="test2", content_type=content_type, codename="test_role2"
        )
        permissions = {role_perm, role_perm2}

        user = User.objects.create(username="test")
        role = Role.objects.create(name="test_role")
        session = Session.objects.create(user=user)

        role.permissions.set(permissions)
        role.save()

        user.roles.set([role])
        user.save()

        session.active_roles.set([role])
        session.save()

    def setUp(self):
        self.user = User.objects.all().first()
        self.role = Role.objects.all().first()
        self.session = Session.objects.all().first()
        self.permissions = Permission.objects.filter(name__in=["test", "test2"])

    def test_role_mixin_new_attributes(self):
        self.assertTrue(hasattr(self.user, "roles"))
        self.assertTrue(hasattr(self.user, "is_superuser"))

    def test_role_mixin_assign_roles(self):
        role = Role.manage.add_role("new_role")

        self.user.assign_roles(role)
        self.user.refresh_from_db()

        self.assertTrue(role in self.user.roles.all())

    def test_role_mixin_assign_roles_string(self):
        with self.assertRaises(ValueError):
            self.user.assign_roles("test_role")

    def test_role_mixin_assign_roles_with_junior_role(self):
        junior_role = Role.manage.add_role("junior_role")
        senior_role = Role.manage.add_role("senior_role")
        incompatible_role = Role.manage.add_role("incompatible_role")

        junior_role.set_senior_role(senior_role)
        incompatible_role.set_incompatible_roles([senior_role, junior_role])

        with self.assertRaises(ValueError):
            self.user.assign_roles(senior_role)

        self.user.assign_roles([junior_role, senior_role])

        with self.assertRaises(ValueError):
            self.user.assign_roles(incompatible_role)

        self.assertTrue(junior_role in self.user.roles.all())
        self.assertTrue(senior_role in self.user.roles.all())

    def test_role_mixin_deassign_roles(self):
        junior_role_1 = Role.manage.add_role("junior_role_1")
        junior_role_2 = Role.manage.add_role("junior_role_2")
        junior_role_3 = Role.manage.add_role("junior_role_3")

        junior_role_1.set_senior_role(junior_role_2)
        junior_role_2.set_senior_role(junior_role_3)

        self.user.roles.set([junior_role_1, junior_role_2, junior_role_3])
        self.user.save()

        user_roles = self.user.roles.all()

        self.assertTrue(junior_role_1 in user_roles)
        self.assertTrue(junior_role_2 in user_roles)
        self.assertTrue(junior_role_3 in user_roles)

        self.user.deassign_roles(junior_role_1)
        self.user.refresh_from_db()

        user_roles = self.user.roles.all()

        self.assertTrue(junior_role_1 not in user_roles)
        self.assertTrue(junior_role_2 not in user_roles)
        self.assertTrue(junior_role_3 not in user_roles)

    def test_role_mixin_deassign_roles_string(self):
        with self.assertRaises(ValueError):
            self.user.deassign_roles("test_role")

    def test_role_mixin_assigned_roles(self):
        self.assertTrue(self.role in self.user.assigned_roles())

    def test_role_mixin_has_active_session(self):
        self.assertTrue(self.user.has_active_session())

    def test_role_mixin_has_active_session_no_session(self):
        self.session.delete()
        self.assertFalse(self.user.has_active_session())

    def test_role_mixin_get_active_session(self):
        self.assertEqual(self.session, self.user.get_active_session())

    def test_role_mixin_get_active_session_by_id(self):
        self.assertEqual(self.session, self.user.get_active_session(self.session.id))

    @override_settings(USE_TZ=False)
    def test_role_mixin_get_active_session_old_session(self):
        self.session.date_start = datetime(1980, 1, 1, 1, 1, 1)
        self.session.save()
        self.assertEqual(None, self.user.get_active_session())

    def test_role_mixin_has_role(self):
        self.assertTrue(self.user.has_role("test_role"))
        self.assertTrue(self.user.has_role(self.role))

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_get_roles_permissions(self):
        self.role.permissions.set([self.permissions[0]])
        self.role2 = Role.objects.create(name="test_role2")
        self.role2.permissions.set([self.permissions[1]])
        self.role2.save()
        self.user.roles.add(*{self.role2})

        roles_permissions = self.user.get_roles_permissions()
        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_get_all_permissions(self):
        roles_permissions = self.user.get_roles_permissions()

        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_has_perms(self):
        self.assertTrue(self.user.has_perm("rbaca.test_role"))
        self.assertFalse(self.user.has_perm("foo.bar"))

        self.assertTrue(self.user.has_perms(["rbaca.test_role", "rbaca.test_role2"]))
        self.assertFalse(self.user.has_perms(["foo.bar", "bar.foo"]))

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_has_module_perms(self):
        self.assertTrue(self.user.has_module_perms("rbaca"))

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_get_roles_permissions_session_based(self):
        self.role.permissions.set([self.permissions[0]])
        self.role.save()

        self.role2 = Role.objects.create(name="test_role2")
        self.role2.permissions.set([self.permissions[1]])
        self.role2.save()

        self.user.roles.add(*{self.role2})
        self.session.active_roles.add(*{self.role2})

        roles_permissions = self.user.get_roles_permissions()
        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_get_all_permissions_session_based(self):
        self.role.permissions.set([self.permissions[0], self.permissions[1]])
        self.role.save()
        roles_permissions = self.user.get_roles_permissions()

        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_has_perms_session_based(self):
        self.role.permissions.set([self.permissions[0]])
        self.role.save()
        self.assertTrue(self.user.has_perm("rbaca.test_role"))
        self.assertFalse(self.user.has_perm("foo.bar"))

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_has_module_perms_session_based(self):
        self.assertTrue(self.user.has_module_perms("rbaca"))

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_get_roles_permissions_superuser(self):
        self.user.is_superuser = True
        self.user.save()

        roles_permissions = self.user.get_roles_permissions()
        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_get_all_permissions_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        roles_permissions = self.user.get_roles_permissions()

        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_has_perms_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.has_perm("rbaca.test_role"))
        self.assertTrue(self.user.has_perm("foo.bar"))

        self.assertTrue(self.user.has_perms(["rbaca.test_role", "rbaca.test_role2"]))
        self.assertTrue(self.user.has_perms(["foo.bar", "bar.foo"]))

    @override_settings(USE_SESSIONS=False)
    def test_role_mixin_has_module_perms_superuser(self):
        self.assertTrue(self.user.has_module_perms("rbaca"))

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_get_roles_permissions_superuser_session_based(self):
        self.user.is_superuser = True
        self.user.save()

        roles_permissions = self.user.get_roles_permissions()
        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_get_all_permissions_superuser_session_based(self):
        self.user.is_superuser = True
        self.user.save()
        roles_permissions = self.user.get_roles_permissions()

        self.assertTrue("rbaca.test_role" in roles_permissions)
        self.assertTrue("rbaca.test_role2" in roles_permissions)

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_has_perms_superuser_session_based(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.has_perm("rbaca.test_role"))
        self.assertTrue(self.user.has_perm("foo.bar"))

        self.assertTrue(self.user.has_perms(["rbaca.test_role", "rbaca.test_role2"]))
        self.assertTrue(self.user.has_perms(["foo.bar", "bar.foo"]))

    @override_settings(USE_SESSIONS=True)
    def test_role_mixin_has_module_perms_superuser_session_based(self):
        self.assertTrue(self.user.has_module_perms("rbaca"))
