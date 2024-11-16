from django.test import TestCase
from rest_framework.serializers import ValidationError
from rest_framework_jwt.utils import jwt_encode_payload

from rbaca.api.serializers import ExpandedTokenVerification
from rbaca.api.utils import jwt_payload_handler
from rbaca.models import Role, User


class TestExpandedTokenVerification(TestCase):
    user_credentials = {"username": "test", "password": "test"}

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", **self.user_credentials
        )
        self.role = Role.objects.create(name="test_role_1")
        self.user.roles.add(*{self.role})
        self.user.save()

    def get_token(self):
        return jwt_encode_payload(jwt_payload_handler(self.user))

    def test_is_valid(self):
        token = self.get_token()
        data = {"token": token, "node": "test_node_1"}
        serializer = ExpandedTokenVerification(data=data)

        self.assertTrue(serializer.is_valid())

        self.assertEqual(
            serializer.validate(data),
            {"token": token, "user": self.user, "node_access": ["test_node_1"]},
        )

        data = {"token": token, "node": "test_node_2"}
        serializer = ExpandedTokenVerification(data=data)

        self.assertFalse(serializer.is_valid())

        with self.assertRaises(ValidationError):
            serializer.validate(data)

        serializer = ExpandedTokenVerification(data={"token": token})

        self.assertFalse(serializer.is_valid())

        with self.assertRaises(ValidationError):
            serializer.validate(data)
