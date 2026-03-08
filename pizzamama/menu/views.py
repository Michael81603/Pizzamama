from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommandeForm, ConnexionForm, InscriptionForm, SuiviCommandeForm
from .models import Categorie, Commande, Pizza
from .services.cart import (
    add_pizza_to_cart,
    build_cart_context,
    clear_cart,
    decrease_pizza_quantity,
    remove_pizza_from_cart,
)
from .services.orders import create_order_from_form, get_order_report_data


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("menu")


def liste_pizzas(request, categorie_id=None):
    categories = Categorie.objects.all()
    categorie_active = None
    query = request.GET.get("q", "").strip()
    pizzas = Pizza.objects.select_related("categorie").all()

    if categorie_id:
        categorie_active = get_object_or_404(Categorie, id=categorie_id)
        pizzas = pizzas.filter(categorie_id=categorie_id)

    if query:
        pizzas = pizzas.filter(Q(nom__icontains=query) | Q(description__icontains=query))

    cart_context = build_cart_context(request.session)

    return render(
        request,
        "menu/liste_pizzas.html",
        {
            "categories": categories,
            "pizzas": pizzas,
            "categorie_active": categorie_active,
            "query": query,
            **cart_context,
        },
    )


@require_POST
def ajouter_panier(request, pizza_id):
    pizza = get_object_or_404(Pizza, id=pizza_id)
    add_pizza_to_cart(request.session, pizza)
    return redirect(_safe_next_url(request))


@require_POST
def diminuer_panier(request, pizza_id):
    decrease_pizza_quantity(request.session, pizza_id)
    return redirect(_safe_next_url(request))


@require_POST
def supprimer_panier(request, pizza_id):
    remove_pizza_from_cart(request.session, pizza_id)
    return redirect(_safe_next_url(request))


@require_POST
def vider_panier(request):
    clear_cart(request.session)
    return redirect(_safe_next_url(request))


def validation_commande(request):
    cart_context = build_cart_context(request.session)
    panier = cart_context["panier"]

    if not panier:
        messages.warning(request, "Votre panier est vide.")
        return redirect("menu")

    initial = {}
    if request.user.is_authenticated:
        initial["nom"] = request.user.get_full_name() or request.user.username
        initial["email"] = request.user.email

    if request.method == "POST":
        form = CommandeForm(request.POST)
        if form.is_valid():
            commande = create_order_from_form(
                form=form,
                cart=panier,
                user=request.user if request.user.is_authenticated else None,
            )
            clear_cart(request.session)
            request.session["derniere_commande_ref"] = commande.reference
            messages.success(
                request,
                f"Merci {commande.nom}. Commande {commande.reference} enregistree.",
            )
            return redirect(f"{reverse('confirmation_commande')}?ref={commande.reference}")
    else:
        form = CommandeForm(initial=initial)

    return render(
        request,
        "menu/validation_commande.html",
        {"form": form, **cart_context},
    )


def confirmation_commande(request):
    reference = request.GET.get("ref") or request.session.get("derniere_commande_ref")
    commande = None
    if reference:
        commande = Commande.objects.prefetch_related("items").filter(reference__iexact=reference).first()
    return render(request, "menu/confirmation_commande.html", {"commande": commande})


def inscription(request):
    if request.user.is_authenticated:
        return redirect("menu")

    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte cree avec succes.")
            return redirect("menu")
    else:
        form = InscriptionForm()

    return render(request, "menu/inscription.html", {"form": form})


def connexion(request):
    if request.user.is_authenticated:
        return redirect("menu")

    form = ConnexionForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Connexion reussie.")
        return redirect(_safe_next_url(request))

    return render(request, "menu/connexion.html", {"form": form})


@require_POST
def deconnexion(request):
    logout(request)
    messages.info(request, "Vous etes deconnecte.")
    return redirect("menu")


@login_required
def mes_commandes(request):
    commandes = Commande.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "menu/mes_commandes.html", {"commandes": commandes})


def suivi_commande(request):
    form = SuiviCommandeForm(request.GET or None)
    commande = None

    if form.is_bound and form.is_valid():
        commande = (
            Commande.objects.prefetch_related("items")
            .filter(
                reference__iexact=form.cleaned_data["reference"],
                email__iexact=form.cleaned_data["email"],
            )
            .first()
        )
        if commande is None:
            messages.error(request, "Aucune commande trouvee avec ces informations.")

    return render(request, "menu/suivi_commande.html", {"form": form, "commande": commande})


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_staff)
def rapport_commandes(request):
    return render(request, "menu/rapport_commandes.html", get_order_report_data())


def A_propos(request):
    return render(request, "menu/A_propos.html", {"support_email": settings.DEFAULT_FROM_EMAIL})
