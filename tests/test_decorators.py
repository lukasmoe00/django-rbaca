from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from rbaca.decorators import attribute_required, role_required, session_required
from rbaca.models import Role, Session, User


@override_settings(ROOT_URLCONF="rbaca.urls", USE_SESSIONS=False)
class TestRoleRequired(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.factory = RequestFactory()

        self.role = Role.objects.create(name="test_role")

        self.user.roles.add(*{self.role})
        self.user.save()

    def test_role_required_has_role(self):
        @role_required("test_role")
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_role_required_has_not_role(self):
        @role_required("test_role2")
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)

    def test_role_required_has_not_role_with_excaption(self):
        @role_required("test_role2", raise_exception=True)
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            test_view(request)


@override_settings(ROOT_URLCONF="rbaca.urls", USE_SESSIONS=True)
class TestSessionRequired(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.factory = RequestFactory()

        self.role = Role.objects.create(name="test_role")

        self.user.roles.add(*{self.role})
        self.user.save()

        self.session = Session.objects.create(user=self.user)
        self.session.active_roles.add(*{self.role})
        self.session.save()

    def test_session_required_with_session(self):
        @session_required()
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_session_required_without_session(self):
        self.session.delete()

        @session_required()
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)

    @override_settings(USE_SESSIONS=False)
    def test_session_required_without_session_settings(self):
        self.session.delete()

        @session_required()
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF="rbaca.urls")
class TestAttributeRequired(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def has_user_id(self):
        return lambda u, k: u.id == 1

    def has_not_user_id(self):
        return lambda u, k: u.id == -1

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.factory = RequestFactory()

        self.role = Role.objects.create(name="test_role")

        self.user.roles.add(*{self.role})
        self.user.save()

    def test_attribute_required_matching_ids(self):
        @attribute_required(self.has_user_id())
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_attribute_required_not_matching_ids(self):
        @attribute_required(self.has_not_user_id())
        def test_view(request):
            return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = test_view(request)
        self.assertEqual(response.status_code, 302)
