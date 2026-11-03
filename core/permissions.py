from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import PerfilUsuario

# Verifica se é funcionario

def eh_funcionario(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    perfil = PerfilUsuario.objects.filter(usuario=user).first()
    return bool(perfil and perfil.eh_funcionario)


def funcionario_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not eh_funcionario(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
