from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Carrinho, PerfilUsuario

# Ao cadastrar um novo usuario, é criado uma instancia de perfil e carrinho para ele

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_perfil_e_carrinho(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.get_or_create(usuario=instance)
        Carrinho.objects.get_or_create(usuario=instance)
