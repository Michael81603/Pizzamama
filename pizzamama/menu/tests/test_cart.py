from django.test import TestCase
from django.urls import reverse

from menu.tests.helpers import TempMediaMixin, create_pizza


class CartViewsTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.pizza = create_pizza()

    def _add_to_cart(self, next_url=None):
        return self.client.post(
            reverse("ajouter_panier", args=[self.pizza.id]),
            data={"next": next_url or reverse("menu")},
        )

    def test_add_and_decrease_cart(self):
        self._add_to_cart()
        self._add_to_cart()

        session = self.client.session
        self.assertEqual(session["panier"][str(self.pizza.id)]["quantite"], 2)

        self.client.post(reverse("diminuer_panier", args=[self.pizza.id]), data={"next": reverse("menu")})
        session = self.client.session
        self.assertEqual(session["panier"][str(self.pizza.id)]["quantite"], 1)

        self.client.post(reverse("diminuer_panier", args=[self.pizza.id]), data={"next": reverse("menu")})
        session = self.client.session
        self.assertNotIn(str(self.pizza.id), session.get("panier", {}))

    def test_clear_cart_empties_session(self):
        self._add_to_cart()
        self.client.post(reverse("vider_panier"), data={"next": reverse("menu")})
        self.assertEqual(self.client.session.get("panier"), {})

    def test_unsafe_next_redirects_to_menu(self):
        response = self.client.post(
            reverse("ajouter_panier", args=[self.pizza.id]),
            data={"next": "https://evil.example.com"},
        )
        self.assertRedirects(response, reverse("menu"))
