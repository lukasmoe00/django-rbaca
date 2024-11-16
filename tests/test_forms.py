from django.contrib.auth.models import Permission
from django.test import TestCase

from rbaca.forms import RoleExpirationForm, RoleForm, UserRoleForm
from rbaca.models import Role, User


class TestRoleForm(TestCase):
    def setUp(self):
        self.junior_role = Role.objects.create(name="junior_role")
        self.incompatible_role = Role.objects.create(name="incompatible_role")

    def test_correct_data(self):
        form_data = {
            "name": "senior_role",
            "permissions": [],
            "incompatible_roles": [2],
        }
        form = RoleForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_senior_role_in_incompatible_roles(self):
        form_data = {
            "name": "junior_role_2",
            "senior_role": 1,
            "permissions": [],
            "incompatible_roles": [1],
        }
        form = RoleForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestUserRoleForm(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.junior_role = Role.objects.create(name="junior")
        self.senior_role = Role.objects.create(name="senior")
        self.junior_role.senior_role = self.senior_role
        self.junior_role.save()
        self.incompatible_role = Role.objects.create(name="incompatible_role")
        self.incompatible_role.incompatible_roles.set(
            [self.junior_role, self.senior_role]
        )
        self.incompatible_role.save()

        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )

    def test_correct_data(self):
        form_data = {"roles": [1]}
        form = UserRoleForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_junior_role(self):
        form_data = {"roles": [2]}
        form = UserRoleForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_incompatible_roles_selected(self):
        form_data = {"roles": [1, 2, 3]}
        form = UserRoleForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestRoleExpirationForm(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.junior_role = Role.objects.create(name="junior")
        self.senior_role = Role.objects.create(name="senior")
        self.junior_role.senior_role = self.senior_role
        self.junior_role.save()
        self.incompatible_role = Role.objects.create(name="incompatible_role")
        self.incompatible_role.incompatible_roles.set(
            [self.senior_role, self.senior_role]
        )
        self.incompatible_role.save()

        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )

    def test_correct_data(self):
        form_data = {
            "role": self.junior_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_role_selection(self):
        form_data = {
            "role": self.senior_role.id + 1,
            "expiration_date": "",
        }
        form = RoleExpirationForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())

    def test_save_method(self):
        form_data = {
            "role": self.junior_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

        role_expiration = form.save()

        self.assertEqual(role_expiration.role, self.junior_role)
        self.assertEqual(role_expiration.user, self.user)
        self.assertEqual(
            role_expiration.expiration_date.strftime("%Y-%m-%d"), "2023-12-31"
        )
        self.assertTrue(self.user.roles.filter(id=self.junior_role.id).exists())

        role_expiration.delete()

    def test_save_method_adding_senior_role(self):
        form_data = {
            "role": self.senior_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

        role_expiration = form.save()

        self.assertEqual(role_expiration.role, self.senior_role)
        self.assertEqual(role_expiration.user, self.user)
        self.assertEqual(
            role_expiration.expiration_date.strftime("%Y-%m-%d"), "2023-12-31"
        )
        self.assertTrue(self.user.roles.filter(id=self.junior_role.id).exists())
        self.assertTrue(self.user.roles.filter(id=self.senior_role.id).exists())

        role_expiration.delete()

    def test_allow_superroles(self):
        assign_role = Permission.objects.get(codename="assign_role")
        assignable_role = Role.objects.create(name="assignable_role")
        assignable_role.permissions.add(assign_role)

        form_data = {
            "role": assignable_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.user, allow_superroles=True, data=form_data)
        self.assertTrue(form.is_valid())

        form = RoleExpirationForm(
            user=self.user, allow_superroles=False, data=form_data
        )
        self.assertFalse(form.is_valid())

    def test_roles_to_exclude(self):
        Role.objects.create(name="excluded_role1")
        Role.objects.create(name="excluded_role2")

        form_data = {
            "role": self.junior_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())

        form = RoleExpirationForm(
            user=self.user,
            roles_to_exclude=["junior", "excluded_role1"],
            data=form_data,
        )
        self.assertFalse(form.is_valid())

        form = RoleExpirationForm(
            user=self.user,
            roles_to_exclude=["excluded_role1", "excluded_role2"],
            data=form_data,
        )
        self.assertTrue(form.is_valid())

    def test_adding_role_to_superuser(self):
        self.user_credentials["username"] = "admin"
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", **self.user_credentials
        )
        form_data = {
            "role": self.junior_role.id,
            "expiration_date": "2023-12-31",
        }
        form = RoleExpirationForm(user=self.superuser, data=form_data)
        self.assertTrue(not form.is_valid())
