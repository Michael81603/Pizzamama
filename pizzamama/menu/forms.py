from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import Commande


User = get_user_model()


class CommandeForm(forms.ModelForm):
    telephone = forms.CharField(
        label="Telephone",
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9 ]{8,15}$",
                message="Numero de telephone invalide (8 a 15 chiffres).",
            )
        ],
    )

    class Meta:
        model = Commande
        fields = ["nom", "email", "telephone", "adresse", "payment_method", "notes"]
        labels = {
            "nom": "Nom complet",
            "email": "Adresse email",
            "adresse": "Adresse de livraison",
            "payment_method": "Mode de paiement",
            "notes": "Instructions complementaires",
        }
        widgets = {
            "adresse": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Ex: Lot II M 15, Antananarivo"}
            ),
            "notes": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Code portail, etage, repere..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "nom": "Votre nom complet",
            "email": "vous@example.com",
            "telephone": "+261 34 00 000 00",
        }
        autocomplete = {
            "nom": "name",
            "email": "email",
            "telephone": "tel",
            "adresse": "street-address",
        }
        for name, field in self.fields.items():
            css_class = "form-select" if name == "payment_method" else "form-control"
            field.widget.attrs.setdefault("class", css_class)
            if name in placeholders:
                field.widget.attrs.setdefault("placeholder", placeholders[name])
            if name in autocomplete:
                field.widget.attrs.setdefault("autocomplete", autocomplete[name])

    def clean_nom(self):
        nom = self.cleaned_data["nom"].strip()
        if len(nom) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caracteres.")
        return nom

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_telephone(self):
        telephone = " ".join(self.cleaned_data["telephone"].split())
        if len(telephone.replace(" ", "")) < 8:
            raise ValidationError("Numero de telephone invalide.")
        return telephone

    def clean_adresse(self):
        adresse = self.cleaned_data["adresse"].strip()
        if len(adresse) < 10:
            raise ValidationError("L'adresse doit contenir au moins 10 caracteres.")
        return adresse

    def clean_notes(self):
        return self.cleaned_data["notes"].strip()


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Choisissez un identifiant",
            "email": "vous@example.com",
        }
        autocomplete = {
            "username": "username",
            "email": "email",
            "password1": "new-password",
            "password2": "new-password",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            if name in placeholders:
                field.widget.attrs.setdefault("placeholder", placeholders[name])
            field.widget.attrs.setdefault("autocomplete", autocomplete.get(name, "off"))
        self.fields["username"].label = "Nom d'utilisateur"
        self.fields["email"].label = "Adresse email"
        self.fields["password1"].label = "Mot de passe"
        self.fields["password2"].label = "Confirmation du mot de passe"

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Cet email est deja utilise.")
        return email


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.setdefault("class", "form-control")
        self.fields["username"].widget.attrs.setdefault("autocomplete", "username")
        self.fields["username"].widget.attrs.setdefault("placeholder", "Votre identifiant")
        self.fields["password"].widget.attrs.setdefault("class", "form-control")
        self.fields["password"].widget.attrs.setdefault("autocomplete", "current-password")
        self.fields["password"].widget.attrs.setdefault("placeholder", "Votre mot de passe")


class SuiviCommandeForm(forms.Form):
    reference = forms.CharField(max_length=20, label="Reference de commande")
    email = forms.EmailField(label="Email de commande")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "reference": "Ex: PM260307ABC123",
            "email": "email utilise a la commande",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("placeholder", placeholders.get(name, ""))

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
