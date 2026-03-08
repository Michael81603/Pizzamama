from django.test import TestCase

from menu.forms import CommandeForm, SuiviCommandeForm
from menu.tests.helpers import order_payload


class FormValidationTests(TestCase):
    def test_commande_form_rejects_invalid_phone(self):
        form = CommandeForm(data=order_payload(telephone="abc"))
        self.assertFalse(form.is_valid())
        self.assertIn("telephone", form.errors)

    def test_commande_form_normalizes_values(self):
        form = CommandeForm(
            data=order_payload(
                email="CLIENT@EXAMPLE.COM ",
                notes="  Sonner deux fois.  ",
            )
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "client@example.com")
        self.assertEqual(form.cleaned_data["notes"], "Sonner deux fois.")

    def test_suivi_form_normalizes_reference_and_email(self):
        form = SuiviCommandeForm(data={"reference": " pm123abc ", "email": "TEST@EXAMPLE.COM "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["reference"], "PM123ABC")
        self.assertEqual(form.cleaned_data["email"], "test@example.com")
