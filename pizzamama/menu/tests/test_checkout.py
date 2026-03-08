from django.test import TestCase
from django.urls import reverse

from menu.models import Commande, CommandeItem
from menu.tests.helpers import TempMediaMixin, create_pizza, order_payload


class CheckoutFlowTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.pizza = create_pizza()

    def _add_to_cart(self):
        return self.client.post(
            reverse("ajouter_panier", args=[self.pizza.id]),
            data={"next": reverse("menu")},
        )

    def test_empty_cart_redirects_from_checkout(self):
        response = self.client.get(reverse("validation_commande"))
        self.assertRedirects(response, reverse("menu"))

    def test_validation_commande_creates_order_and_items_and_clears_cart(self):
        self._add_to_cart()

        response = self.client.post(reverse("validation_commande"), data=order_payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("confirmation_commande")))

        commande = Commande.objects.get()
        self.assertTrue(commande.reference)
        self.assertEqual(commande.payment_status, Commande.PaiementStatut.EN_ATTENTE)
        self.assertEqual(CommandeItem.objects.filter(commande=commande).count(), 1)
        self.assertEqual(self.client.session.get("panier"), {})

    def test_confirmation_commande_uses_reference_querystring(self):
        self._add_to_cart()
        self.client.post(reverse("validation_commande"), data=order_payload())
        commande = Commande.objects.get()

        response = self.client.get(reverse("confirmation_commande"), data={"ref": commande.reference})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, commande.reference)
