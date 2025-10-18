from django.shortcuts import render, redirect, get_object_or_404
from .models import Categorie, Pizza, CommandeItem, Commande
from django.contrib import messages


def liste_pizzas(request, categorie_id=None):
    categories = Categorie.objects.all()
    categorie_active = None
    query = request.GET.get("q", "")
    if categorie_id:
        categorie_active = get_object_or_404(Categorie, id=categorie_id)
        pizzas = Pizza.objects.filter(categorie_id=categorie_id)
    else:
        pizzas = Pizza.objects.all()

    if query:
        pizzas = pizzas.filter(nom__icontains=query)

    panier = request.session.get("panier", {})
    total = sum(float(item["prix"]) * item["quantite"] for item in panier.values())

    return render(request, "liste_pizzas.html", {
        "categories": categories,
        "pizzas": pizzas,
        "panier": panier,
        "total": total,
        "categorie_active": categorie_active,
        "query": query,
    })


def ajouter_panier(request, pizza_id):
    pizza = get_object_or_404(Pizza, id=pizza_id)
    panier = request.session.get("panier", {})

    if str(pizza_id) in panier:
        panier[str(pizza_id)]["quantite"] += 1
    else:
        panier[str(pizza_id)] = {
            "nom": pizza.nom,
            "prix": float(pizza.prix),
            "quantite": 1,
        }

    request.session["panier"] = panier
    return redirect("menu")


def supprimer_panier(request, pizza_id):
    panier = request.session.get("panier", {})
    if str(pizza_id) in panier:
        del panier[str(pizza_id)]
    request.session["panier"] = panier
    return redirect("menu")


def vider_panier(request):
    request.session["panier"] = {}
    return redirect("menu")



def validation_commande(request):
    panier = request.session.get("panier", {})
    total = sum(float(item["prix"]) * item["quantite"] for item in panier.values())

    if not panier:
        messages.warning(request, "Votre panier est vide !")
        return redirect("menu")

    if request.method == "POST":
        nom = request.POST.get("nom")
        email = request.POST.get("email")
        adresse = request.POST.get("adresse")
        telephone = request.POST.get("telephone")

        if not nom or not email or not adresse:
            messages.error(request, "Veuillez remplir tous les champs.")
            return redirect("validation_commande")

        # ✅ Créer la commande principale
        commande = Commande.objects.create(
            nom=nom,
            email=email,
            adresse=adresse,
            telephone=telephone,
            total=total
        )

        # ✅ Enregistrer chaque item du panier
        for item in panier.values():
            CommandeItem.objects.create(
                commande=commande,
                pizza_nom=item["nom"],
                prix=item["prix"],
                quantite=item["quantite"]
            )

        # 🧹 Vider le panier
        request.session["panier"] = {}

        # ✅ Message de confirmation
        messages.success(request, f"Merci {nom} ! Votre commande a été enregistrée avec succès.")
        return redirect("confirmation_commande")

    return render(request, "validation_commande.html", {"panier": panier, "total": total})


def confirmation_commande(request):
    return render(request, "confirmation_commande.html")

def A_propos(request):
    return render(request, "A_propos.html")

def contact(request):
    return render(request, "contact.html")