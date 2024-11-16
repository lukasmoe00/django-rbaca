from django.urls import path
from rest_framework_jwt import views as jwt_views

from rbaca import views
from rbaca.api import views as api_views

urlpatterns = [
    path("role/<int:pk>/", views.RoleDetail.as_view(), name="role_view"),
    path("role/create/", views.RoleCreate.as_view(), name="role_create"),
    path("role/<int:pk>/update/", views.RoleUpdate.as_view(), name="role_update"),
    path("role/<int:pk>/delete/", views.RoleDelete.as_view(), name="role_delete"),
    path("role/list/", views.RoleList.as_view(), name="role_list"),
    path(
        "user/<int:pk>/update",
        views.UserRoleUpdate.as_view(),
        name="role_user_update",
    ),
    path(
        "get-node-access-token/",
        jwt_views.ObtainJSONWebTokenView.as_view(),
        name="get_node_jwt",
    ),
    path(
        "refresh-node-access-token/",
        jwt_views.RefreshJSONWebTokenView.as_view(),
        name="verify_node_jwt",
    ),
    path(
        "verify-node-access-token/",
        api_views.VerifyNodeAcces.as_view(),
        name="refresh_node_jwt",
    ),
]
