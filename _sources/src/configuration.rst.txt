Configuration
=============

Django settings for RBAC-A
--------------------------

To configure `django-rbaca` within your Django project, you need to make adjustments in your project's settings.
The following settings are relevant for the integration and configuration of `django-rbaca`. All settings must be set.

1. Add `django-rbaca` to your installed apps:

   .. code-block:: python
      :linenos:

      INSTALLED_APPS = [
         ...
         "rbaca",
      ]

2. Add or set the role-based backend:

   .. code-block:: python
      :linenos:

      AUTHENTICATION_BACKENDS = [
         ...
         "rbaca.backends.RoleBackend",
      ]

3. Enable/disable sessions:

   .. code-block:: python
      :linenos:

      USE_SESSIONS = True/False

4. Set the timeout for sessions:

   .. code-block:: python
      :linenos:

      SESSION_TIMEOUT_ABSOLUTE = INT_IN_SECONDS

Custom User Model and Role-Based Access
---------------------------------------

In many Django projects, the default user model provided by Django (`django.contrib.auth.models.User`)
may not be configured properly to seamlessly integrate with Role-Based Access Control (RBAC) using `django-rbaca`.
To ensure that your user model aligns with the RBAC requirements, it's often necessary to customize it.
Here are your primary options for achieving this compatibility:

1. **Inherit the RoleMixin**:

    One approach is to inherit the `RoleMixin` from `rbaca.models` in your custom user model.
    This mixin provides the necessary fields and methods for handling roles associated with users.
    By extending your user model with `RoleMixin`, you can efficiently manage user-role assignments and access control.

    Example:

    .. code-block:: python
      :linenos:

      from django.contrib.auth.models import AbstractUser
      from rbaca.models import RoleMixin

      class CustomUser(AbstractUser, RoleMixin):
          # Your custom user model fields and methods

2. **Use the AbstractRoleUser**:

    `django-rbaca` offers the `AbstractRoleUser` model, which you can use as the base for your custom user model.
    This abstract model extends Django's `AbstractUser` and includes the necessary role-related fields.
    By inheriting from `AbstractRoleUser`, your user model becomes fully compatible with RBAC-A.

    Example:

   .. code-block:: python
      :linenos:

      from rbaca.models import AbstractRoleUser

      class CustomUser(AbstractRoleUser):
           # Your custom user model fields and methods

3. **Use the User Model from the rbaca app**:

    Another option is to utilize the custom user model provided by the `django-rbaca` app.
    This user model, named `User`, comes pre-configured to work seamlessly with RBAC.
    Using the `User` model can simplify the setup process and ensure compatibility with
    `django-rbaca` without the need for further customizations.

    Example:

   .. code-block:: python
      :linenos:

      AUTH_USER_MODEL = "rbaca.models.user"

Choosing the right approach depends on your project's specific needs and existing user model structure.
Ensure that your custom user model provides a many-to-many relationship with roles, allowing for the
assignment of roles to users and precise control over access permissions.

Whichever option you select, it's crucial to define your user model properly to enable
effective Role-Based Access Control with `django-rbaca`. Your choice should align with the
requirements and complexities of your project while maintaining the integrity of your access control system.


Distributed Access Control
--------------------------

`django-rbaca` offers the capability to implement distributed access control, allowing you to manage permissions
in distributed systems. This is especially valuable when your application spans multiple services, applications, or components.

To utilize Distributed Access Control with `django-rbaca`, you can take advantage of the API endpoints
it provides for permission checks. You need to integrate these endpoints into your distributed system
and ensure they are protected and accessible as required.

First of all, `djangorestframework` and `drf-jwt` is required for this and it needs to be configured.

1. Add JWT to your `djangorestframework` configuration in the django settings:

   .. code-block:: python
        :linenos:

         'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
         ...
         )

2. Configure drf-jwt in the django settings:

   .. code-block:: python
        :linenos:

         JWT_AUTH = {
            'JWT_PAYLOAD_HANDLER': 'rbaca.api.utils.jwt_payload_handler',
         }

3. Configure your node access in the django settings:

   .. code-block:: python
        :linenos:

         NODE_ACCESS = {
            "your_node_1": ["your", "roles"],
            "your_node_2": ["your_roles"],
         }

4. Include the API urls into the urls.py of the django project:

   .. code-block:: python
        :linenos:

         from django.conf.urls import url
         from django.urls import include, path
         from rbaca import urls as rbaca_urls


         urlpatterns = [
            path("rbaca/", include((rbaca_urls, "rbaca"))),
         ]

Now you can use these API endpoints:

- **`rbaca/get-node-access-token/`**: Get a JWT, user credentials are required to obtain a token.
- **`rbaca/refresh-node-access-token/`**: Refresh the JWT, user credentials are required to obtain a token.
- **`rbaca/verify-node-access-token/`**: Check if the given token is valid for the current node, node name is required as a parameter.

You can manually check these urls, to get a better understanding on how to use them properly.
