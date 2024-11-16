# boot_django.py
#
# This file sets up and configures Django. It's used by scripts that need to
# execute as if running in a Django server.
import os

import django


def boot_django():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
