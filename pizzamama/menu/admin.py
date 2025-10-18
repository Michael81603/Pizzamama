from django.contrib import admin
from .models import Pizza, Categorie, Commande, CommandeItem
# Register your models here.

admin.site.register(Categorie)
admin.site.register(Pizza)

admin.site.site_header = "Pizzamama Administration"
admin.site.site_title = "Pizzamama Admin"
admin.site.index_title = "Bienvenue dans la gestion du site"


class CommandeItemInline(admin.TabularInline):
    model = CommandeItem
    extra = 0

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email','adresse','telephone', 'total', 'date_commande')
    inlines = [CommandeItemInline]