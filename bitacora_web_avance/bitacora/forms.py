from django import forms


class LoginForm(forms.Form):
    usuario = forms.CharField(
        max_length=80,
        label="Usuario institucional",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    clave = forms.CharField(
        max_length=128,
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
            }
        ),
    )

    def clean_usuario(self):
        return self.cleaned_data["usuario"].strip()