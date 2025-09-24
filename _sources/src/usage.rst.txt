.. _Usage:

Usage
=====

Roles
-----
In the context of `django-rbaca`, roles play a fundamental role in determining and managing user access
and permissions within your Django application. Roles serve as a mechanism to categorize users into distinct groups,
each with specific responsibilities, permissions, and access levels. Understanding the concept of roles and their
significance is key to effective access control and security in your application.

Roles offer several key advantages within your application:

- **Granular Access Control**: Roles enable granular control over who can perform specific actions and access particular functionalities. This fine-grained control enhances security and privacy.

- **Simplified Management**: Managing user access and permissions becomes more straightforward when roles are well-defined. Roles streamline the process of determining what each user can and cannot do.

- **Scalability**: As your application grows, roles allow you to easily accommodate new user types or responsibilities without rewriting access control rules for each user.

- **Customization**: Roles can be customized to fit the unique requirements of your application. You can create roles that align with your specific use cases and business logic.

- **Dynamic Access**: The ability to dynamically assign, modify, and remove roles from users allows for dynamic and real-time adjustments to access permissions.

To effectively use `django-rbaca`, it's essential to define roles and manage their associated permissions.
This section provides examples of how to define roles and assign permissions in your Django project.


1. Defining roles

    .. code-block:: python
        :linenos:

        from rbaca.models import Role

        # Create a new role
        admin_role = Role.objects.create(name='admin')

        # Assign permissions to the role
        admin_role.permissions.add('can_view_dashboard', 'can_manage_users')

2. Assigning permissions to a user
    .. code-block:: python
        :linenos:

        from your.models.user import User
        from rbaca.models import Role

        # Get a user
        user = User.objects.get(username='example_user')

        # Assign a role to the user
        user.roles.add(Role.objects.get(name='admin'))
        user.save()

Sessions
--------

In `django-rbaca`, a session represents the active roles associated with a user during their current session.
The active roles determine the permissions that the user has for the duration of the session.
This mechanism allows for dynamic control over a user's access based on the specific roles assigned to them.

When managing user sessions with `django-rbaca`, keep the following considerations in mind:

- **Role-Based Session Initialization**: Upon user authentication, initialize the session with the appropriate roles assigned to the user. This ensures that the user has access only to the functionalities corresponding to their roles during the session.

- **Dynamic Role Updates**: Handle any dynamic changes to a user's roles during the session. If a user's roles are modified while the session is active, ensure that the session reflects these changes to adjust the user's access permissions accordingly.

- **Session Termination**: Define proper procedures for terminating user sessions. When a user logs out or their session expires, clear the active roles associated with the session to prevent any unauthorized access attempts. This app provides functionalities to start and stop sessions.

`django-rbaca` simplifies the management of user sessions within the context of Role-Based Access Control,
ensuring that users have access only to functionalities corresponding to their active roles.
By leveraging the session management capabilities of `django-rbaca`, you can maintain a secure and controlled
environment for your application, allowing for precise and dynamic access control throughout a user's session.

In the following sections, we'll explore how to manage sessions effectively within the `django-rbaca` app,
enabling you to maximize the security and efficiency of your application's access control mechanisms.

1. Start a session

    .. code-block:: python
        :linenos:

        from rbaca.models import Session

        # Create a session
        Session.manage.add_session(user, RoleQuerySet)

2. Check if user has active session

    .. code-block:: python
        :linenos:

        if user.has_active_session():
            return secrets
        else:
            return None

3. Manage session roles
    .. code-block:: python
        :linenos:

        session = user.get_active_session()

        if session:
            # remove active roles
            session.drop_active_roles()

            # add roles
            session.add_active_roles(RoleQuerySet)

4. End a session
    .. code-block:: python
        :linenos:

        session = user.get_active_session()

        # Close session
        session.close()


Role Expiration
---------------
In the `django-rbaca` app, Role Expiration is a powerful feature that enables dynamic and controlled management
of user roles within your application. Role Expiration introduces the concept of time-limited or time-bound roles,
allowing you to set specific validity periods for roles assigned to users. Understanding Role Expiration and
its significance is crucial for optimizing access control and security in your application.

The Role Expiration feature offers several key advantages within your application:

- **Temporary Privileges**: Role Expiration is particularly useful for roles that grant temporary or conditional privileges. For example, you might have roles that provide access for a specific project or event, and these roles automatically expire when the project or event concludes.

- **Security Enhancement**: Role Expiration enhances security by ensuring that users have access only when it is explicitly granted. This feature minimizes the risk of unintended or prolonged access to sensitive functionalities.

- **Dynamic Access Control**: Role Expiration allows for dynamic changes in user access based on time. This feature is valuable when dealing with roles that have predefined durations, such as temporary admin roles during system maintenance.

- **Administrative Ease**: Managing time-bound roles becomes more straightforward with Role Expiration. Roles with fixed expiration dates can be automatically deactivated, reducing the need for manual intervention.

The dynamic and time-sensitive nature of Role Expiration adds an extra layer of control and precision to your access
management strategy, allowing for tailored and secure user access based on predefined timeframes. Here are some examples:

1. Define an role expiration

    .. code-block:: python
        :linenos:

        from datetime import date
        from rbaca.models import RoleExpiration

        RoleExpiration.objects.create(user=user, role=role, expiration_date=date.today())

2. Get all expired roles
    .. code-block:: python
        :linenos:

        from rbaca.models import RoleExpiration

        RoleExpiration.manage.get_expired_roles()

2. Remove all expired roles
    .. code-block:: python
        :linenos:

        from rbaca.models import RoleExpiration

        RoleExpiration.manage.remove_expired_roles()

Securing Views
--------------

Configuring permissions and roles for class-based views in your project ensures that only authorized users can
access specific parts. To set permissions and roles required for class-based views:

1. Open your Django views or viewsets where you want to set permissions and roles.

2. Use the `PermissionRequiredMixin` to specify the required permissions for the view. For example:

   .. code-block:: python
    :linenos:

      from django.contrib.auth.mixins import PermissionRequiredMixin

      class MyView(PermissionRequiredMixin, View):
          permission_required = "app_name.permission_codename"

          def get(self, request):
              # View logic here

   Replace `"app_name.permission_codename"` with the actual permission codename for the view.
   You can also provide a list of permissions.

3. Use the `RoleRequiredMixin` to specify the required role(s) for the view. For example:

   .. code-block:: python
    :linenos:

      from rbaca.mixins import RoleRequiredMixin

      class MyView(RoleRequiredMixin, View):
          role_required = "Role Name"

          def get(self, request):
              # View logic here

   Replace `"Role Name"` with the name of the required role. You can also provide a list of roles.

4. Use the `AttributeRequiredMixin` to specify the required attribute for the view. For example:

   .. code-block:: python
    :linenos:

      from rbaca.mixins import AttributeRequiredMixin

      class MyView(AttributeRequiredMixin, View):
          check_func = function

          def get(self, request):
              # View logic here

   Replace `function` with comparing function. This function should look like this `function(user, **kwargs)`,
   where `user` is the user to check the permissions for and `**kwargs` is a dictionary containing additional information
   if needed. For more details, read the docs of django-rbaca.


5. Save your changes, and the permissions and roles will now be enforced when accessing the class-based views.

    It's important to note that you must configure the roles and permissions before applying them to class-based views. `django-rbaca` is
    fully compatible with Django's Access Control, for example with the `has_perm` decorator or `PermissionRequiredMixin`.

Securing Templates
------------------
Configuring permissions and roles for templates in your project ensures that only authorized users can
access specific parts. To set permissions and roles required for templates:

1. Open your Django views or viewsets where you want to set permissions and roles.

2. Use the `has_perm` to specify the required permissions for the view. For example:

   .. code-block:: python
    :linenos:

    {% load rbaca_tags %}

    {% if has_perm request.user 'app.can_edit_post' %}
        <a href="{% url 'edit_post' post.id %}">Edit Post</a>
    {% endif %}

3. Use the `has_role` to specify the required role(s) for the view. For example:

   .. code-block:: python
        :linenos:

        {% load rbaca_tags %}

        {% if has_role request.user 'Editor' %}
            <a href="{% url 'edit_post' post.id %}">Edit Post</a>
        {% endif %}

4. Use the `has_active_session` to check if the current user has an active session.

    .. code-block:: python
        :linenos:

        {% load rbaca_tags %}

        {% if has_active_session request.user %}
            <a href="{% url 'secrets' %}">Secrets</a>
        {% endif %}

Making Migrations
-----------------

In Antonn, database migrations are essential for keeping your database schema up-to-date with model
changes of the auth manager app.
To create new migrations, you should use the `makemigrations.py` script.

1. Open a terminal or command prompt.

2. Navigate to the root of auth manager app

3. Run the following command to create new migrations:

.. code-block:: bash

    python makemigrations.py

This command will create a new database migration, which reflects the model changes.

Running Tests
-------------

Testing is a crucial aspect of software development to ensure that the application works
correctly and reliably.
The auth manager app provides the ability to run tests using the `run_tests.py` script.

1. Open a terminal or command prompt.

2. Navigate to the root of auth manager app

3. Run the following command to execute all available tests::

.. code-block:: bash

    python run_tests.py

This script uses test settings, to ensure that everythin runs correctly.

Conclusion
----------
django-rbaca is a powerful app to manage permissions within a django project.
This part of the documentation is just an introduction of the main mechanisms.
For a detailed documentation of all functionalities and features, take a look at the "Modules" section.
