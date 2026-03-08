from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from menu.models import Commande


class AccountAndTrackingTests(TestCase):
    def test_mes_commandes_requires_login(self):
        response = self.client.get(reverse("mes_commandes"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("connexion"), response.url)

    def test_mes_commandes_for_authenticated_user(self):
        user = User.objects.create_user(username="micka", password="StrongPass123")
        commande = Commande.objects.create(
            user=user,
            nom="Micka",
            email="micka@example.com",
            adresse="Antananarivo centre",
            telephone="+261340000001",
            total="30000.00",
        )
        self.client.login(username="micka", password="StrongPass123")

        response = self.client.get(reverse("mes_commandes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, commande.reference)

    def test_suivi_commande_by_reference_and_email(self):
        commande = Commande.objects.create(
            nom="Client Public",
            email="public@example.com",
            adresse="Adresse test complete",
            telephone="+261340000002",
            total="18000.00",
        )
        response = self.client.get(
            reverse("suivi_commande"),
            data={"reference": commande.reference.lower(), "email": commande.email.upper()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, commande.reference)

    def test_staff_report_requires_staff(self):
        user = User.objects.create_user(username="client", password="StrongPass123")
        self.client.login(username="client", password="StrongPass123")

        response = self.client.get(reverse("rapport_commandes"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("connexion"), response.url)

    def test_staff_report_is_available(self):
        staff = User.objects.create_user(username="admin", password="StrongPass123", is_staff=True)
        self.client.login(username="admin", password="StrongPass123")

        response = self.client.get(reverse("rapport_commandes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rapport des commandes")
