# Pizza Mama

Application Django pour presenter le catalogue Pizza Mama, prendre les commandes, suivre les statuts et consulter un rapport simple cote staff.

## Structure

- `pizzamama/manage.py`: point d'entree Django.
- `pizzamama/pizzamama/settings/`: configuration separee en `base`, `dev` et `prod`.
- `pizzamama/menu/services/`: logique panier, creation de commande et reporting.
- `pizzamama/menu/templates/menu/`: templates reorganises autour d'un `base.html` partage.
- `pizzamama/menu/tests/`: suite de tests decoupee par domaine fonctionnel.

## Demarrage local

1. Creer ou activer un environnement virtuel.
2. Installer les dependances:
   `pip install -r requirements.txt`
3. Copier `.env.example` vers `.env` et ajuster les variables.
4. Lancer les migrations:
   `python manage.py migrate`
5. Demarrer le serveur:
   `python manage.py runserver`

## Commandes utiles

- `python manage.py test`
- `python manage.py check`
- `python manage.py check --deploy --settings=pizzamama.settings.prod`

## Notes

- Le paiement numerique n'est pas integre a un prestataire: les commandes sont donc creees avec un statut de paiement `En attente` jusqu'a validation manuelle.
- Les uploads locaux et les fichiers `staticfiles/` sont ignores par Git.
