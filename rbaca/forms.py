from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import DateInput, ModelForm
from django.utils.translation import gettext_lazy as _

from rbaca.models import Role, RoleExpiration

UserModel = get_user_model()


class RoleForm(ModelForm):
    """
    This form is used to create or update Role objects.
    It includes validation to ensure that incompatible roles are not selected.
    """

    class Meta:
        model = Role
        fields = "__all__"

    def clean_incompatible_roles(self):
        """
        Custom validation method to ensure that a senior role cannot be selected as an incompatible role.

        Returns:
            The cleaned data for incompatible roles.

        Raises:
            ValidationError if a senior role is selected as an incompatible role.
        """
        incompatible_roles = self.cleaned_data["incompatible_roles"]
        senior_role = self.cleaned_data["senior_role"]

        if senior_role in incompatible_roles:
            raise ValidationError(_("A senior role can not be an incompatible role"))

        return incompatible_roles


class UserRoleForm(ModelForm):
    """
    This form is used to assign roles to a user. It includes validation to ensure that
    the user has all junior roles and that the selected role is compatible with the user's roles.
    """

    class Meta:
        model = UserModel
        fields = ["roles"]

    def clean_roles(self):
        """
        Custom validation method to ensure that the selected roles are compatible and that
        the user has all junior roles.

        Returns:
            The cleaned data for selected roles.

        Raises:
            ValidationError if the selected roles are incompatible or if the user does not have all junior roles.
        """

        roles = self.cleaned_data["roles"]
        if Role.manage.check_role_compatibility(roles):
            return self.cleaned_data["roles"]
        else:
            raise ValidationError(
                "Invalid role selection."
                + " Make sure that the user has all junior roles and that the selected"
                + " role is compatible with the users roles"
            )


class RoleExpirationForm(ModelForm):
    """
    This form is used to create RoleExpiration objects.
    It provides dynamic queryset filtering based on user attributes and includes
    validation for role compatibility.

    Attributes:
        user (User): The user for whom the form is being displayed.
        allow_superroles (bool): A boolean indicating whether superroles are allowed.
        roles_to_exclude (List[str]): A list of role names to be excluded from selection.
    """

    class Meta:
        model = RoleExpiration
        fields = ["role", "expiration_date"]
        labels = {"role": "role (selecting a senior role will add all junior roles)"}
        widgets = {
            "expiration_date": DateInput(attrs={"type": "date"}),
        }

    def __init__(
        self, user, allow_superroles=False, roles_to_exclude=[], *args, **kwargs
    ):
        """
        Initializes the form with a dynamic queryset based on user attributes.

        Args:
            user (User): The user for whom the form is being displayed.
            allow_superroles (bool): A boolean indicating whether superroles are allowed.
            roles_to_exclude (List[str]): A list of role names to be excluded from selection.
        """
        super().__init__(*args, **kwargs)
        self.user = user
        user_role_ids = user.roles.values_list("id", flat=True)
        incompatible_role_ids = user.roles.values_list(
            "incompatible_roles__id", flat=True
        )
        if allow_superroles:
            assignable_roles_ids = Role.objects.none().values_list("id", flat=True)
        else:
            assignable_roles_ids = Role.objects.filter(
                permissions__codename="assign_role"
            ).values_list("id", flat=True)

        role_ids_to_exclude = Role.objects.filter(
            name__in=roles_to_exclude
        ).values_list("id", flat=True)

        all_ids_to_exclude = (
            set(incompatible_role_ids)
            | set(assignable_roles_ids)
            | set(user_role_ids)
            | set(role_ids_to_exclude)
        )

        self.fields["role"].queryset = Role.objects.all().exclude(
            id__in=all_ids_to_exclude
        )
        self.fields["role"].empty_label = None

    def clean_role(self):
        """
        Custom validation method to ensure that the selected role is compatible and that the user has all junior roles.

        Returns:
            The cleaned data for the selected role.

        Raises:
            ValidationError if the selected role is incompatible or if the user does not have all junior roles.
        """
        selected_role = Role.objects.filter(id=self.cleaned_data["role"].id)
        roles = (
            self.user.roles.all()
            | selected_role
            | Role.objects.filter(
                id__in=[role.id for role in selected_role[0].get_all_junior_roles()]
            )
        )
        if Role.manage.check_role_compatibility(
            roles, False, True
        ) and not self.user.has_role(selected_role[0]):
            return self.cleaned_data["role"]
        else:
            if self.user.is_active and self.user.is_superuser:
                raise ValidationError(
                    "Cannot assign roles to superuser. Superuser own all permissions without roles."
                )
            else:
                raise ValidationError(
                    "Invalid role selection."
                    + " Make sure that the selected role is compatible with the users roles"
                )

    def save(self, commit=True):
        """
        Overrides the save method to ensure the selected role is added to the user's roles.
        """
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            senior_role = self.cleaned_data["role"]
            junior_roles = self.cleaned_data["role"].get_all_junior_roles()

            for role in junior_roles:
                if role not in self.user.roles.all():
                    self.user.roles.add(role)
                    RoleExpiration.objects.create(
                        expiration_date=instance.expiration_date,
                        user=instance.user,
                        role=role,
                    )
            if senior_role not in self.user.roles.all():
                self.user.roles.add(senior_role)
            instance.save()
        return instance
