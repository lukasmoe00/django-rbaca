from django.test import TestCase

from rbaca.api.utils import jwt_payload_handler
from rbaca.models import User


class TestUtils(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )

    def test_jwt_payload_handler(self):
        payload = jwt_payload_handler(self.user)

        self.assertTrue(isinstance(payload, dict))
        self.assertEqual(payload.get("user_id"), self.user.pk)
        self.assertEqual(payload.get("username"), self.user.username)
        self.assertTrue("exp" in payload)
