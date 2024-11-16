from calendar import timegm
from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_jwt.utils import jwt_encode_payload

from rbaca.api.utils import jwt_payload_handler
from rbaca.models import Role, User


@override_settings(ROOT_URLCONF="rbaca.urls")
class TestVerifyNodeAcces(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.role = Role.objects.create(name="test_role_1")
        self.role2 = Role.objects.create(name="test_role_2")

        self.user.roles.set([self.role])
        self.user.save()
        self.user.refresh_from_db()

    def get_token(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            "/get-node-access-token/", self.user_credentials, format="json"
        )

        return response.data["token"]

    def create_token(self, user, exp=None, orig_iat=None):
        payload = jwt_payload_handler(user)

        if exp:
            payload["exp"] = exp

        if orig_iat:
            payload["orig_iat"] = timegm(orig_iat.utctimetuple())

        token = jwt_encode_payload(payload)

        return token

    def test_valid_token(self):
        client = APIClient(enforce_csrf_checks=True)
        token = self.get_token()

        response = client.post(
            "/verify-node-access-token/",
            {"token": token, "node": "test_node_1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.data["token"], token)

    def test_no_access_to_other_node(self):
        client = APIClient(enforce_csrf_checks=True)
        token = self.get_token()

        response = client.post(
            "/verify-node-access-token/",
            {"token": token, "node": "test_node_2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_has_access_to_all_nodes(self):
        admin = User.objects.create(
            username="admin",
            email="admin@example.com",
            password="password",
            is_superuser=True,
        )

        client = APIClient(enforce_csrf_checks=True)
        token = self.create_token(admin)

        response = client.post(
            "/verify-node-access-token/",
            {"token": token, "node": "test_node_1"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = client.post(
            "/verify-node-access-token/",
            {"token": token, "node": "test_node_2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_fails_with_expired_token(self):
        client = APIClient(enforce_csrf_checks=True)

        token = self.create_token(
            self.user,
            exp=datetime.utcnow() - timedelta(seconds=5),
            orig_iat=datetime.utcnow() - timedelta(hours=1),
        )

        response = client.post(
            "/verify-node-access-token/", {"token": token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fails_with_bad_token(self):
        client = APIClient(enforce_csrf_checks=True)

        token = "fake-token"

        response = client.post(
            "/verify-node-access-token/", {"token": token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fails_with_missing_user(self):
        client = APIClient(enforce_csrf_checks=True)

        user = User.objects.create_user(
            email="example@example.com", username="example", password="password"
        )

        token = self.create_token(user)
        user.delete()

        response = client.post(
            "/verify-node-access-token/", {"token": token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
