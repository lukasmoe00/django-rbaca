from django.contrib import admin

from rbaca.models import Role, RoleExpiration, Session

admin.site.register(Role)
admin.site.register(Session)
admin.site.register(RoleExpiration)
