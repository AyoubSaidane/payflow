from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth import password_validation

from accounts.models import User


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name',
                  'last_name',
                  'email',
                  'telephone',
                  ]

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name',
                  'last_name',
                  'email',
                  'telephone',
                  ]


class UserSearchForm(forms.Form):
    """
    This is the user search form.
    """
    query = forms.CharField(label="Recherche", required=False, widget=forms.TextInput(attrs={"placeholder": "Recherche..."}))
    statut = forms.ChoiceField(label="Statut", choices=(("active", "Utilisateur actifs"), ("inactive", "Utilisateurs archivés")), required=False)


class SignUpForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """

    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete":"new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirmation de mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete":"new-password"}),
        strip=False,
        help_text="Saisir le même mot de passe une deuxième fois",
    )

    class Meta:
        model = User
        fields = ("first_name","last_name","email",)

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name:
            raise forms.ValidationError("Merci de compléter votre prénom")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not last_name:
            raise forms.ValidationError("Merci de compléter votre nom")
        return last_name

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Merci de taper deux fois le même mot de passe", code='password_mismatch')
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user