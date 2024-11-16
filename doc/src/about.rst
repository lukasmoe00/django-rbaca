About
=====

Purpose
-------

The `django-rbaca` library is designed to provide robust and flexible Role-Based Access Control (RBAC) for
Django web applications. RBAC is a powerful mechanism for managing user access and permissions,
and `django-rbaca` aims to simplify the implementation of RBAC in your Django projects.

Features
--------

- **Role Definition**: Easily define and manage roles for your application either through the admin interface or programmatically. `django-rbaca` provides many model methods to handle the logic in the model layer.

- **Permission Assignment**: Assign specific permissions to roles, granting or restricting access to various parts of your application. Based on Django's Permission model.

- **Access Control Decorators and Mixins**: Restrict access to views by applying RBAC decorators and mixins to your Django view functions or classes, either with a single permission or many roles.

- **Template Tags**: Control the visibility of elements within your templates based on user roles and permissions using RBAC template tags.

- **Role Based Backend**: `django-rbaca` provides a comprehensive Role Based Backend for managing role-based access control (RBAC) within your Django application. This feature allows you to define, assign, and enforce roles, ensuring controlled access to different parts of your application.

- **Distributed Access Control**:  `django-rbaca` provides API endpoints to check for permission in distributed knots with JSON Web Tokens, based on the REST Framework for Django.
Getting Started
---------------

To get started with `django-rbaca`, refer to the :ref:`Installation` and :ref:`Configuration` sections in the main documentation. These sections will guide you through the initial setup and configuration steps. Once you have `django-rbaca` up and running, you can begin defining roles, assigning permissions, and securing your application.
