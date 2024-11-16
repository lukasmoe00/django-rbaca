from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from rbaca.forms import RoleForm, UserRoleForm
from rbaca.models import Role

UserModel = get_user_model()


class RoleList(PermissionRequiredMixin, ListView):
    """
    View to list all roles.

    This view displays a list of all available roles.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.view_role").
        model (Role): The model used for listing roles.
    """

    permission_required = "rbaca.view_role"
    model = Role


class RoleDetail(PermissionRequiredMixin, DetailView):
    """
    View to display role details.

    This view displays the details of a specific role.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.view_role").
        model (Role): The model used for displaying role details.
    """

    permission_required = "rbaca.view_role"
    model = Role


class RoleCreate(PermissionRequiredMixin, CreateView):
    """
    View to create a new role.

    This view allows users to create a new role.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.add_role").
    """

    permission_required = "rbaca.add_role"

    def get(self, request, *args, **kwargs):
        context = {"form": RoleForm()}
        return render(request, "rbaca/role_form.html", context)

    def post(self, request, *args, **kwargs):
        form = RoleForm(request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy("rbaca:role_list"))
        return render(request, "rbaca/role_form.html", {"form": form})


class RoleUpdate(PermissionRequiredMixin, UpdateView):
    """
    View to update a role.

    This view allows users to update an existing role.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.change_role").
    """

    permission_required = "rbaca.change_role"

    def get(self, request, pk, *args, **kwargs):
        context = {"form": RoleForm(instance=Role.objects.filter(pk=pk).first())}
        return render(request, "rbaca/role_form.html", context)

    def post(self, request, pk, *args, **kwargs):
        form = RoleForm(request.POST, instance=Role.objects.filter(pk=pk).first())

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy("rbaca:role_list"))
        return render(request, "rbaca/role_form.html", {"form": form})


class RoleDelete(PermissionRequiredMixin, DeleteView):
    """
    View to delete a role.

    This view allows users to delete an existing role.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.delete_role").
        model (Role): The model used for deleting roles.
        success_url (str): The URL to redirect to after successfully deleting a role.
    """

    permission_required = "rbaca.delete_role"
    model = Role
    success_url = reverse_lazy("rbaca:role_list")


class UserRoleUpdate(PermissionRequiredMixin, UpdateView):
    """
    View to update a user's roles.

    This view allows users to update the roles assigned to a specific user.

    Attributes:
        permission_required (str): The permission required to access this view ("rbaca.assign_role").
    """

    permission_required = "rbaca.assign_role"

    def get(self, request, pk, *args, **kwargs):
        context = {
            "form": UserRoleForm(instance=UserModel.objects.filter(pk=pk).first())
        }
        return render(request, "rbaca/role_form.html", context)

    def post(self, request, pk, *args, **kwargs):
        form = UserRoleForm(
            request.POST, instance=UserModel.objects.filter(pk=pk).first()
        )
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse_lazy("rbaca:role_list"))

        return render(request, "rbaca/role_form.html", {"form": form})
