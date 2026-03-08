from django.contrib import admin
from django.db.models import Count

from .models import Categorie, Commande, CommandeItem, Pizza

admin.site.site_header = "Pizzamama Administration"
admin.site.site_title = "Pizzamama Admin"
admin.site.index_title = "Gestion du site"


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "prix")
    list_filter = ("categorie",)
    search_fields = ("nom", "description")
    ordering = ("categorie__nom", "nom")
    list_select_related = ("categorie",)


class CommandeItemInline(admin.TabularInline):
    model = CommandeItem
    extra = 0
    readonly_fields = ("pizza_nom", "prix", "quantite", "total")
    can_delete = False


@admin.action(description="Marquer en preparation")
def mark_preparation(modeladmin, request, queryset):
    del modeladmin, request
    queryset.update(status=Commande.Statut.EN_PREPARATION)


@admin.action(description="Marquer en livraison")
def mark_livraison(modeladmin, request, queryset):
    del modeladmin, request
    queryset.update(status=Commande.Statut.EN_LIVRAISON)


@admin.action(description="Marquer livree")
def mark_livree(modeladmin, request, queryset):
    del modeladmin, request
    queryset.update(status=Commande.Statut.LIVREE)


@admin.action(description="Marquer paiement paye")
def mark_paid(modeladmin, request, queryset):
    del modeladmin, request
    queryset.update(payment_status=Commande.PaiementStatut.PAYE)


@admin.action(description="Marquer annulee")
def mark_cancelled(modeladmin, request, queryset):
    del modeladmin, request
    queryset.update(status=Commande.Statut.ANNULEE)


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "nom",
        "total_articles",
        "telephone",
        "status",
        "payment_method",
        "payment_status",
        "total",
        "date_commande",
    )
    list_filter = ("status", "payment_method", "payment_status", "date_commande")
    list_editable = ("status", "payment_status")
    search_fields = ("reference", "nom", "email", "telephone")
    readonly_fields = ("reference", "date_commande", "updated_at", "user", "total")
    inlines = [CommandeItemInline]
    actions = [mark_preparation, mark_livraison, mark_livree, mark_paid, mark_cancelled]
    date_hierarchy = "date_commande"
    list_select_related = ("user",)
    ordering = ("-date_commande",)
    autocomplete_fields = ("user",)
    search_help_text = "Recherche par reference, nom, email ou telephone."
    fieldsets = (
        ("Identification", {"fields": ("reference", "user", "nom", "email", "telephone")}),
        ("Livraison", {"fields": ("adresse", "notes")}),
        ("Statut", {"fields": ("status", "payment_method", "payment_status", "total")}),
        ("Horodatage", {"fields": ("date_commande", "updated_at")}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").annotate(item_count=Count("items"))

    @admin.display(description="Articles", ordering="item_count")
    def total_articles(self, obj):
        return obj.item_count
