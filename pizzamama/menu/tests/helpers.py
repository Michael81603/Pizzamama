import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from menu.models import Categorie, Pizza


class TempMediaMixin:
    def setUp(self):
        super().setUp()
        self._temp_media_dir = tempfile.mkdtemp()
        self._media_override = override_settings(MEDIA_ROOT=self._temp_media_dir)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._temp_media_dir, ignore_errors=True)
        super().tearDown()


def create_pizza(*, category_name="Classiques", nom="Margherita", prix="25000.00"):
    categorie = Categorie.objects.create(nom=category_name)
    return Pizza.objects.create(
        nom=nom,
        description="Tomate, fromage",
        prix=prix,
        image=SimpleUploadedFile("pizza.jpg", b"fake-image-content", content_type="image/jpeg"),
        categorie=categorie,
    )


def order_payload(**overrides):
    payload = {
        "nom": "Client Test",
        "email": "client@example.com",
        "telephone": "+261340000000",
        "adresse": "Lot IIA 12, Antananarivo",
        "payment_method": "mobile_money",
        "notes": "Appeler avant livraison",
    }
    payload.update(overrides)
    return payload
