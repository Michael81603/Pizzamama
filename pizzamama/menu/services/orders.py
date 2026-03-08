import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from menu.models import Commande, CommandeItem
from menu.services.cart import get_cart_lines


logger = logging.getLogger(__name__)
ZERO = Decimal("0.00")


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

    total = sum((line["line_total"] for line in cart_lines), ZERO).quantize(Decimal("0.01"))

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


def get_order_report_data():
    today = timezone.localdate()
    start_of_month = today.replace(day=1)
    orders = Commande.objects.all()

    stats_global = orders.aggregate(
        nb=Count("id"),
        ca=Coalesce(Sum("total"), ZERO),
    )
    stats_day = orders.filter(date_commande__date=today).aggregate(
        nb=Count("id"),
        ca=Coalesce(Sum("total"), ZERO),
    )
    stats_month = orders.filter(date_commande__date__gte=start_of_month).aggregate(
        nb=Count("id"),
        ca=Coalesce(Sum("total"), ZERO),
    )

    status_labels = dict(Commande.Statut.choices)
    raw_status_breakdown = orders.values("status").annotate(total=Count("id")).order_by("-total")
    status_breakdown = [
        {"label": status_labels.get(item["status"], item["status"]), "total": item["total"]}
        for item in raw_status_breakdown
    ]

    payment_labels = dict(Commande.PaiementStatut.choices)
    raw_payment_breakdown = orders.values("payment_status").annotate(total=Count("id")).order_by("-total")
    payment_breakdown = [
        {
            "label": payment_labels.get(item["payment_status"], item["payment_status"]),
            "total": item["total"],
        }
        for item in raw_payment_breakdown
    ]

    revenue_expression = ExpressionWrapper(
        F("prix") * F("quantite"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    top_pizzas = (
        CommandeItem.objects.annotate(line_total=revenue_expression)
        .values("pizza_nom")
        .annotate(
            quantite=Coalesce(Sum("quantite"), 0),
            ca=Coalesce(Sum("line_total"), ZERO),
        )
        .order_by("-quantite", "-ca")[:5]
    )
    recent_orders = Commande.objects.prefetch_related("items")[:5]

    return {
        "stats_global": stats_global,
        "stats_jour": stats_day,
        "stats_mois": stats_month,
        "status_breakdown": status_breakdown,
        "payment_breakdown": payment_breakdown,
        "top_pizzas": top_pizzas,
        "recent_orders": recent_orders,
    }

