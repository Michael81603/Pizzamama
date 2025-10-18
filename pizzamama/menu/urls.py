from django.urls import path
from . import views

urlpatterns = [
    path("menu/", views.liste_pizzas, name="menu"),
    path("categorie/<int:categorie_id>/", views.liste_pizzas, name="menu_par_categorie"),

    path("ajouter_panier/<int:pizza_id>/", views.ajouter_panier, name="ajouter_panier"),
    path("supprimer_panier/<int:pizza_id>/", views.supprimer_panier, name="supprimer_panier"),
    path("vider_panier/", views.vider_panier, name="vider_panier"),

    path('commande/confirmation/', views.confirmation_commande, name='confirmation_commande'),
    path('commande/validation/', views.validation_commande, name='validation_commande'),

    path('', views.A_propos, name="A_propos"),

]
