from django.urls import path
from . import views

urlpatterns = [
    path("", views.A_propos, name="A_propos"),

    path("menu/", views.liste_pizzas, name="menu"),
    path("categorie/<int:categorie_id>/", views.liste_pizzas, name="menu_par_categorie"),

    path("ajouter_panier/<int:pizza_id>/", views.ajouter_panier, name="ajouter_panier"),
    path("diminuer_panier/<int:pizza_id>/", views.diminuer_panier, name="diminuer_panier"),
    path("supprimer_panier/<int:pizza_id>/", views.supprimer_panier, name="supprimer_panier"),
    path("vider_panier/", views.vider_panier, name="vider_panier"),

    path("commande/validation/", views.validation_commande, name="validation_commande"),
    path("commande/confirmation/", views.confirmation_commande, name="confirmation_commande"),
    path("suivi-commande/", views.suivi_commande, name="suivi_commande"),

    path("compte/inscription/", views.inscription, name="inscription"),
    path("compte/connexion/", views.connexion, name="connexion"),
    path("compte/deconnexion/", views.deconnexion, name="deconnexion"),
    path("mes-commandes/", views.mes_commandes, name="mes_commandes"),

    path("rapport/", views.rapport_commandes, name="rapport_commandes"),
]
