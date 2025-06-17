import random
import string
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    """
    Customisation du modèle d'utilisateur de Django
    """
    email = models.EmailField(
        _('email address'),
        null=True
    )

    nb_biens = models.IntegerField(null=True, blank=True)
    particulier = models.BooleanField(null=True)
    protection_ponctuelle = models.BooleanField(null=True)
    societe = models.CharField(verbose_name="Société", max_length=40, null=True)



    is_admin = models.BooleanField(default=False)

    uuid = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    telephone = models.CharField(verbose_name="Numéro de téléphone", null=True, blank=True, max_length=100)

    notification_mail = models.BooleanField(verbose_name="Activer les notifications par mail", default=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["last_name"]
        verbose_name = "Utilisateur"

    def __str__(self):
        return self.get_full_name()


    def get_full_name(self):
        """
        Returns the user full name or a representation of its identity.
        """
        if self.first_name or self.last_name:
            if self.first_name and self.last_name:
                return '{} {}'.format(self.first_name, self.last_name)
            else:
                return '{}{}'.format(self.first_name, self.last_name)
        elif self.email:
            return self.email
        else:
            return self.username


