from rest_framework import serializers
from rest_framework_jwt.serializers import VerifyAuthTokenSerializer
from rest_framework_jwt.utils import check_payload, check_user


class ExpandedTokenVerification(VerifyAuthTokenSerializer):
    node = serializers.CharField()


class ExpandedTokenVerification(ExpandedTokenVerification):
    """
    Custom serializer for expanded token verification, including node access.

    This serializer is used to verify JWT tokens with additional node access
    information.
    """

    def _check_node_access(self, payload, node):
        """
        Check if the token payload contains access to the specified node.

        Args:
            payload (Dict): The decoded token payload.
            node (str): The node you want to access.

        Returns:
            node_access (List[str]): List of nodes the token has access to.

        Raises:
            serializers.ValidationError: If the token is invalid or lacks access
                to the requested node.
        """
        node_access = payload.get("node_access")

        if node_access is None:
            raise serializers.ValidationError("Token is invalid.")

        if node is None:
            raise serializers.ValidationError("Accessed node not specified.")

        if node not in node_access:
            raise serializers.ValidationError(
                "Token has no access to the requested node."
            )

        return node_access

    def validate(self, attrs):
        """
        Validates the token and returns user and node access.

        Args:
            attrs (Dict): A dictionary containing token and node information.

        Returns:
            result (Dict): A dictionary containing token, user, and node_access.

        Raises:
            serializers.ValidationError: If token validation fails.
        """
        token = attrs["token"]
        node = attrs["node"]

        payload = check_payload(token=token)
        user = check_user(payload=payload)
        node_access = self._check_node_access(payload=payload, node=node)

        return {"token": token, "user": user, "node_access": node_access}
