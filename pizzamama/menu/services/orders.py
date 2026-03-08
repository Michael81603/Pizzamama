import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from menu.models import Categorie, Commande, CommandeItem, Pizza
from menu.services.cart import get_cart_lines


logger = logging.getLogger(__name__)
ZERO = Decimal("0.00")
TWOPLACES = Decimal("0.01")


def _quantize_amount(value):
    if value in (None, ""):
        return ZERO
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def resolve_payment_status(payment_method):
    del payment_method
    return Commande.PaiementStatut.EN_ATTENTE


def _send_email(*, subject, message, recipients):
    if not recipients:
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Unable to send email '%s' to %s", subject, recipients)


def send_order_notifications(commande):
    if not getattr(settings, "ORDER_NOTIFICATIONS_ENABLED", True):
        return

    client_message = (
        f"Bonjour {commande.nom},\n\n"
        f"Votre commande {commande.reference} a bien ete enregistree.\n"
        f"Montant total: {commande.total} Ar\n"
        f"Statut: {commande.get_status_display()}\n"
        f"Paiement: {commande.get_payment_method_display()} ({commande.get_payment_status_display()})\n\n"
        "Merci pour votre confiance."
    )
    _send_email(
        subject=f"Confirmation commande {commande.reference}",
        message=client_message,
        recipients=[commande.email],
    )

    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", "")
    if admin_email:
        admin_message = (
            f"Commande: {commande.reference}\n"
            f"Client: {commande.nom} ({commande.email})\n"
            f"Telephone: {commande.telephone}\n"
            f"Total: {commande.total} Ar\n"
            f"Adresse: {commande.adresse}\n"
            f"Paiement: {commande.get_payment_method_display()} ({commande.get_payment_status_display()})"
        )
        _send_email(
            subject=f"Nouvelle commande {commande.reference}",
            message=admin_message,
            recipients=[admin_email],
        )


def create_order_from_form(*, form, cart, user=None):
    cart_lines = get_cart_lines(cart)
    if not cart_lines:
        raise ValueError("Cannot create an order from an empty cart.")

    total = sum((line["line_total"] for line in cart_lines), ZERO).quantize(TWOPLACES)

    with transaction.atomic():
        commande = form.save(commit=False)
        if user is not None and getattr(user, "is_authenticated", False):
            commande.user = user
        commande.total = total
        commande.payment_status = resolve_payment_status(commande.payment_method)
        commande.save()

        CommandeItem.objects.bulk_create(
            [
                CommandeItem(
                    commande=commande,
                    pizza_nom=line["nom"],
                    prix=line["prix"],
                    quantite=line["quantite"],
                )
                for line in cart_lines
            ]
        )

        transaction.on_commit(lambda: send_order_notifications(commande))

    return commande


def get_storefront_highlights():
    featured_name_rows = list(
        CommandeItem.objects.values("pizza_nom")
        .annotate(quantite=Coalesce(Sum("quantite"), 0))
        .order_by("-quantite", "pizza_nom")[:3]
    )
    featured_names = [row["pizza_nom"] for row in featured_name_rows]
    featured_map = {
        pizza.nom: pizza
        for pizza in Pizza.objects.select_related("categorie").filter(nom__in=featured_names)
    }
    featured_pizzas = [featured_map[name] for name in featured_names if name in featured_map]

    if len(featured_pizzas) < 3:
        existing_ids = [pizza.id for pizza in featured_pizzas]
        fallback_pizzas = list(
            Pizza.objects.select_related("categorie").exclude(id__in=existing_ids)[: 3 - len(featured_pizzas)]
        )
        featured_pizzas.extend(fallback_pizzas)

    category_highlights = list(
        Categorie.objects.annotate(pizza_count=Count("pizzas"))
        .filter(pizzas__isnull=False)
        .distinct()[:4]
    )
    for category in category_highlights:
        category.cover = category.pizzas.order_by("nom").first()

    business_stats = {
        "pizza_count": Pizza.objects.count(),
        "category_count": Categorie.objects.count(),
        "order_count": Commande.objects.count(),
        "average_ticket": _quantize_amount(
            Commande.objects.aggregate(avg=Coalesce(Avg("total"), ZERO))["avg"]
        ),
    }

    return {
        "featured_pizzas": featured_pizzas,
        "category_highlights": category_highlights,
        "business_stats": business_stats,
    }


def _resolve_report_period(period):
    today = timezone.localdate()
    options = {
        "today": {"label": "Aujourd'hui", "start": today, "end": today},
        "7d": {"label": "7 jours", "start": today - timedelta(days=6), "end": today},
        "30d": {"label": "30 jours", "start": today - timedelta(days=29), "end": today},
        "month": {"label": "Ce mois", "start": today.replace(day=1), "end": today},
        "all": {"label": "Historique", "start": None, "end": today},
    }
    selected_key = period if period in options else "30d"
    return selected_key, options[selected_key], [
        {"value": key, "label": value["label"], "active": key == selected_key}
        for key, value in options.items()
    ]


def _filter_orders_by_period(queryset, start_date, end_date):
    if start_date:
        queryset = queryset.filter(date_commande__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date_commande__date__lte=end_date)
    return queryset


def get_order_report_data(period="30d"):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    all_orders = Commande.objects.all()

    selected_period, period_meta, period_options = _resolve_report_period(period)
    filtered_orders = _filter_orders_by_period(all_orders, period_meta["start"], period_meta["end"])

    stats_global = all_orders.aggregate(nb=Count("id"), ca=Coalesce(Sum("total"), ZERO))
    stats_jour = all_orders.filter(date_commande__date=today).aggregate(
        nb=Count("id"),
        ca=Coalesce(Sum("total"), ZERO),
    )
    stats_mois = all_orders.filter(date_commande__date__gte=month_start).aggregate(
        nb=Count("id"),
        ca=Coalesce(Sum("total"), ZERO),
    )
    stats_period = filtered_orders.aggregate(nb=Count("id"), ca=Coalesce(Sum("total"), ZERO))

    order_count = stats_period["nb"] or 0
    revenue = _quantize_amount(stats_period["ca"])
    average_ticket = (revenue / order_count).quantize(TWOPLACES) if order_count else ZERO
    delivered_count = filtered_orders.filter(status=Commande.Statut.LIVREE).count()
    paid_count = filtered_orders.filter(payment_status=Commande.PaiementStatut.PAYE).count()
    completion_rate = int((delivered_count / order_count) * 100) if order_count else 0
    paid_rate = int((paid_count / order_count) * 100) if order_count else 0

    status_labels = dict(Commande.Statut.choices)
    raw_status_breakdown = filtered_orders.values("status").annotate(total=Count("id")).order_by("-total")
    status_breakdown = []
    for item in raw_status_breakdown:
        total = item["total"]
        status_breakdown.append(
            {
                "label": status_labels.get(item["status"], item["status"]),
                "theme": Commande.STATUS_THEMES.get(item["status"], "pending"),
                "total": total,
                "percent": int((total / order_count) * 100) if order_count else 0,
            }
        )

    payment_labels = dict(Commande.PaiementStatut.choices)
    raw_payment_breakdown = (
        filtered_orders.values("payment_status").annotate(total=Count("id")).order_by("-total")
    )
    payment_breakdown = []
    for item in raw_payment_breakdown:
        total = item["total"]
        payment_breakdown.append(
            {
                "label": payment_labels.get(item["payment_status"], item["payment_status"]),
                "theme": Commande.PAYMENT_THEMES.get(item["payment_status"], "pending"),
                "total": total,
                "percent": int((total / order_count) * 100) if order_count else 0,
            }
        )

    items_queryset = CommandeItem.objects.all()
    if period_meta["start"]:
        items_queryset = items_queryset.filter(commande__date_commande__date__gte=period_meta["start"])
    if period_meta["end"]:
        items_queryset = items_queryset.filter(commande__date_commande__date__lte=period_meta["end"])

    revenue_expression = ExpressionWrapper(
        F("prix") * F("quantite"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    top_pizzas = list(
        items_queryset.annotate(line_total=revenue_expression)
        .values("pizza_nom")
        .annotate(
            quantite=Coalesce(Sum("quantite"), 0),
            ca=Coalesce(Sum("line_total"), ZERO),
        )
        .order_by("-quantite", "-ca")[:5]
    )
    max_quantity = max([pizza["quantite"] for pizza in top_pizzas], default=1)
    for pizza in top_pizzas:
        pizza["bar_percent"] = int((pizza["quantite"] / max_quantity) * 100) if max_quantity else 0

    recent_orders = list(filtered_orders.prefetch_related("items")[:6])

    return {
        "stats_global": stats_global,
        "stats_jour": stats_jour,
        "stats_mois": stats_mois,
        "stats_period": stats_period,
        "average_ticket": average_ticket,
        "completion_rate": completion_rate,
        "paid_rate": paid_rate,
        "status_breakdown": status_breakdown,
        "payment_breakdown": payment_breakdown,
        "top_pizzas": top_pizzas,
        "recent_orders": recent_orders,
        "selected_period": selected_period,
        "selected_period_label": period_meta["label"],
        "period_options": period_options,
    }
