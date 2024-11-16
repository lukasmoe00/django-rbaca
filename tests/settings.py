import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "rbaca"))

BASE_DIR = BASE_DIR

SECRET_KEY = "fake-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rbaca",
]

TIME_ZONE = "UTC"

USE_TZ = True

AUTHENTICATION_BACKENDS = ["rbaca.backends.RoleBackend"]

AUTH_USER_MODEL = "rbaca.User"

USE_SESSIONS = False

SESSION_TIMEOUT_ABSOLUTE = 3600

NODE_ACCESS = {
    "test_node_1": ["test_role_1"],
    "test_node_2": ["test_role_2"],
}

JWT_AUTH = {
    "JWT_PAYLOAD_HANDLER": "rbaca.api.utils.jwt_payload_handler",
}
