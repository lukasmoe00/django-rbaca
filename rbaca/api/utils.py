import uuid
from datetime import datetime

from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import get_username_field, unix_epoch

from rbaca.backends import RoleBackend


def jwt_payload_handler(user):
    """
    Custom JWT payload handler.

    This function generates a custom payload for a JWT token, including user
    information and additional data like node access, expiration, and more.

    Args:
        user (User): The user for whom the JWT token is generated.

    Returns:
        payload (Dict): A dictionary containing the JWT payload.

    Note:
        Ensure that the 'api_settings' used here are correctly configured inyour Django project.

    Example:
        ```
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        ```
    """

    username_field = get_username_field()
    username = getattr(user, username_field)
    node_access = RoleBackend().get_node_access(user)
    issued_at_time = datetime.utcnow()
    expiration_time = issued_at_time + api_settings.JWT_EXPIRATION_DELTA

    payload = {
        "user_id": user.pk,
        "username": username,
        "node_access": node_access,
        "iat": unix_epoch(issued_at_time),
        "exp": expiration_time,
    }

    if api_settings.JWT_TOKEN_ID != "off":
        payload["jti"] = uuid.uuid4()

    if api_settings.JWT_PAYLOAD_INCLUDE_USER_ID:
        payload["user_id"] = user.pk

    if hasattr(user, "profile"):
        payload["user_profile_id"] = (user.profile.pk if user.profile else None,)

    if api_settings.JWT_ALLOW_REFRESH:
        payload["orig_iat"] = unix_epoch(issued_at_time)

    if api_settings.JWT_AUDIENCE is not None:
        payload["aud"] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload["iss"] = api_settings.JWT_ISSUER

    return payload
