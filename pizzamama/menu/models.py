from decimal import Decimal
import secrets

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models
from django.db.models import Q
from django.utils import timezone


class Categorie(models.Model):
    nom = models.CharField(max_length=50)

    class Meta:
        ordering = ("nom",)

    def __str__(self):
        return self.nom


class Pizza(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    image = models.ImageField(upload_to="pizzas/")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name="pizzas")

    class Meta:
        ordering = ("nom",)
        indexes = [models.Index(fields=("categorie", "nom"))]

    def __str__(self):
        return self.nom


class Commande(models.Model):
    class Statut(models.TextChoices):
        NOUVELLE = "nouvelle", "Nouvelle"
        EN_PREPARATION = "preparation", "En preparation"
        EN_LIVRAISON = "livraison", "En livraison"
        LIVREE = "livree", "Livree"
        ANNULEE = "annulee", "Annulee"

    class PaiementMethode(models.TextChoices):
        CASH = "cash", "Paiement a la livraison"
        MOBILE_MONEY = "mobile_money", "Mobile money"
        CARTE = "carte", "Carte bancaire"

    class PaiementStatut(models.TextChoices):
        EN_ATTENTE = "pending", "En attente"
        PAYE = "paid", "Paye"
        ECHOUE = "failed", "Echoue"
        REMBOURSE = "refunded", "Rembourse"

    STATUS_RANKS = {
        Statut.NOUVELLE: 1,
        Statut.EN_PREPARATION: 2,
        Statut.EN_LIVRAISON: 3,
        Statut.LIVREE: 4,
        Statut.ANNULEE: 0,
    }
    STATUS_THEMES = {
        Statut.NOUVELLE: "pending",
        Statut.EN_PREPARATION: "accent",
        Statut.EN_LIVRAISON: "brand",
        Statut.LIVREE: "success",
        Statut.ANNULEE: "danger",
    }
    PAYMENT_THEMES = {
        PaiementStatut.EN_ATTENTE: "pending",
        PaiementStatut.PAYE: "success",
        PaiementStatut.ECHOUE: "danger",
        PaiementStatut.REMBOURSE: "accent",
    }
    STATUS_SUMMARIES = {
        Statut.NOUVELLE: "Votre commande a ete recue et attend maintenant la prise en charge de l'equipe.",
        Statut.EN_PREPARATION: "L'equipe cuisine prepare votre commande en ce moment.",
        Statut.EN_LIVRAISON: "Le livreur est en route avec votre commande.",
        Statut.LIVREE: "La commande a ete remise avec succes.",
        Statut.ANNULEE: "La commande a ete interrompue avant livraison.",
    }
    ETA_LABELS = {
        Statut.NOUVELLE: "35 a 45 min",
        Statut.EN_PREPARATION: "20 a 30 min",
        Statut.EN_LIVRAISON: "10 a 15 min",
        Statut.LIVREE: "Livree",
        Statut.ANNULEE: "Interrompue",
    }
    PAYMENT_SUMMARIES = {
        PaiementStatut.EN_ATTENTE: "Le paiement sera confirme par l'equipe ou a la livraison.",
        PaiementStatut.PAYE: "Le paiement est valide.",
        PaiementStatut.ECHOUE: "Le paiement n'a pas pu etre confirme.",
        PaiementStatut.REMBOURSE: "Le paiement a ete rembourse.",
    }

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes",
    )
    reference = models.CharField(max_length=20, blank=True, unique=True, db_index=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.NOUVELLE,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaiementMethode.choices,
        default=PaiementMethode.CASH,
        db_index=True,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaiementStatut.choices,
        default=PaiementStatut.EN_ATTENTE,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    date_commande = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("-date_commande", "-id")
        indexes = [
            models.Index(fields=("date_commande",)),
            models.Index(fields=("status", "payment_status")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="commande_total_gte_0",
            ),
        ]

    @classmethod
    def generate_reference(cls):
        prefix = timezone.now().strftime("PM%y%m%d")
        while True:
            suffix = secrets.token_hex(3).upper()
            candidate = f"{prefix}{suffix}"
            if not cls.objects.filter(reference=candidate).exists():
                return candidate

    def save(self, *args, **kwargs):
        if self.reference or self.pk:
            return super().save(*args, **kwargs)

        last_error = None
        for _ in range(5):
            self.reference = self.generate_reference()
            try:
                return super().save(*args, **kwargs)
            except IntegrityError as exc:
                self.reference = ""
                last_error = exc

        if last_error is not None:
            raise last_error
        return super().save(*args, **kwargs)

    @property
    def status_rank(self):
        return self.STATUS_RANKS.get(self.status, 0)

    @property
    def progress_percent(self):
        progress_map = {
            self.Statut.NOUVELLE: 20,
            self.Statut.EN_PREPARATION: 45,
            self.Statut.EN_LIVRAISON: 75,
            self.Statut.LIVREE: 100,
            self.Statut.ANNULEE: 100,
        }
        return progress_map.get(self.status, 0)

    @property
    def status_theme(self):
        return self.STATUS_THEMES.get(self.status, "pending")

    @property
    def payment_theme(self):
        return self.PAYMENT_THEMES.get(self.payment_status, "pending")

    @property
    def eta_label(self):
        return self.ETA_LABELS.get(self.status, "A confirmer")

    @property
    def status_summary(self):
        return self.STATUS_SUMMARIES.get(self.status, "Statut mis a jour par l'equipe.")

    @property
    def payment_summary(self):
        return self.PAYMENT_SUMMARIES.get(self.payment_status, "Suivi de paiement en cours.")

    def __str__(self):
        return (
            f"{self.reference} - {self.nom} - {self.total} Ar - "
            f"{self.date_commande.strftime('%d/%m/%Y %H:%M')}"
        )


class CommandeItem(models.Model):
    commande = models.ForeignKey(Commande, related_name="items", on_delete=models.CASCADE)
    pizza_nom = models.CharField(max_length=100)
    prix = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("pizza_nom",)
        constraints = [
            models.CheckConstraint(
                condition=Q(prix__gte=0),
                name="commandeitem_prix_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(quantite__gte=1),
                name="commandeitem_quantite_gte_1",
            ),
        ]

    @property
    def total(self):
        return self.prix * self.quantite

    def __str__(self):
        return f"{self.pizza_nom} (x{self.quantite})"
