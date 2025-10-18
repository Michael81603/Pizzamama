from django.db import models
from django.utils import timezone

# Create your models here.
class Categorie(models.Model):
    nom = models.CharField(max_length=50)

    def __str__(self):
        return self.nom

class Pizza(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="pizzas/") 
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name="pizzas")

    def __str__(self):
        return self.nom

class Commande(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    adresse = models.TextField()
    telephone = models.CharField(max_length=15)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    date_commande = models.DateTimeField(default=timezone.now)
    

    def __str__(self):
        return f"Commande de {self.nom} - {self.total}$ - {self.date_commande.strftime('%d/%m/%Y %H:%M')}"

class CommandeItem(models.Model):
    commande = models.ForeignKey(Commande, related_name='items', on_delete=models.CASCADE)
    pizza_nom = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=6, decimal_places=2)
    quantite = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.pizza_nom} (x{self.quantite})"