.. _Installation:

Installation
============
To work with the `django-rbaca` application, you need to install it
into your Python environment. Follow the steps below to set up the application
and its dependencies.

Local building and installation
-------------------------------
After cloning, open your terminal and navigate to the root directory of the `django-rbaca` project:

.. code-block:: bash

    cd path/to/django-rbaca


Replace path/to/django-rbaca with the actual path to the root directory of the project.

First activate your python environment and ensure that `poetry` is installed:

.. code-block:: bash

    pip install poetry

To install the production dependencies and the package itself, run:

.. code-block:: bash

    poetry install

This command will automatically install the necessary packages and dependencies for the
`django-rbaca` application. For installing the development dependencies, run:

.. code-block:: bash

    poetry install --with dev

Congratulations! You've now set up django-rbaca for development and can start
exploring its features and capabilities.

Installation with Pip
---------------------

.. code-block:: bash

    pip install django-rbaca