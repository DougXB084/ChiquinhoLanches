from .models import Carrinho
from .permissions import eh_funcionario


def navegacao(request):
    # Atualiza o número de itens no carrinho e o perfil do usuario logado no momento :)
    user = request.user
    if not user.is_authenticated:
        return {"carrinho_quantidade": 0, "usuario_funcionario": False}

    carrinho = Carrinho.objects.filter(usuario=user).first()
    return {
        "carrinho_quantidade": carrinho.quantidade_total if carrinho else 0,
        "usuario_funcionario": eh_funcionario(user),
    }
