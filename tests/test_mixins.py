from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.views import View

from rbaca.mixins import AttributeRequiredMixin, RoleRequiredMixin, SessionRequiredMixin
from rbaca.models import Role, Session, User


@override_settings(ROOT_URLCONF="rbaca.urls")
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
        class TestView(RoleRequiredMixin, View):
            role_required = "test_role"

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_role_required_has_not_role(self):
        class TestView(RoleRequiredMixin, View):
            role_required = "test_role2"

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            TestView.as_view()(request)

    def test_role_required_no_role(self):
        class TestView(RoleRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(ImproperlyConfigured):
            TestView.as_view()(request)

    def test_role_required_wrong_type(self):
        class TestView(RoleRequiredMixin, View):
            role_required = 0

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(ValueError):
            TestView.as_view()(request)


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
        class TestView(SessionRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_session_required_without_session(self):
        self.session.delete()

        class TestView(SessionRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            TestView.as_view()(request)

    @override_settings(USE_SESSIONS=False)
    def test_session_required_without_session_settings(self):
        self.session.delete()

        class TestView(SessionRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF="rbaca.urls")
class TestAttributeRequired(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def has_user_id(self):
        return staticmethod(lambda u, **kwargs: u.id == 1)

    def has_not_user_id(self):
        return staticmethod(lambda u, **kwargs: u.id == -1)

    def has_user_id_non_static(self, user, **kwargs):
        return user.id == 1

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.factory = RequestFactory()

    def test_attribute_required_matching_ids(self):
        class TestView(AttributeRequiredMixin, View):
            check_func = self.has_user_id()

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_attribute_required_not_matching_ids(self):
        class TestView(AttributeRequiredMixin, View):
            check_func = self.has_not_user_id()

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(PermissionDenied):
            TestView.as_view()(request)

    def test_attribute_no_check_func(self):
        class TestView(AttributeRequiredMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user

        with self.assertRaises(ImproperlyConfigured):
            TestView.as_view()(request)

    def test_attribute_required_with_class_method(self):
        class TestView(AttributeRequiredMixin, View):
            check_func = self.has_user_id_non_static

            def get(self, request, *args, **kwargs):
                return HttpResponse()

        request = self.factory.get("/test")
        request.user = self.user
        response = TestView.as_view()(request)
        self.assertEqual(response.status_code, 200)
