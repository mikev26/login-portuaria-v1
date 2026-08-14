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


class RegistroCombustibleFilterForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=True,
        label="Fecha inicio",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fecha_fin = forms.DateField(
        required=True,
        label="Fecha fin",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError(
                "La fecha de inicio no puede ser posterior a la fecha final."
            )

        return cleaned_data