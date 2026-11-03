from django.db.models import Count, Q
from django.shortcuts import redirect, render

from .models import Categoria, Pedido, Produto
from .permissions import eh_funcionario


def home(request):
    # Funcionário usa a versão da cantina do site.
    if eh_funcionario(request.user):
        return redirect("pedidos:painel")

    destaques = (
        Produto.objects.filter(ativo=True, estoque__gt=0)
        .select_related("categoria")
        .annotate(
            vendidos=Count(
                "itens_pedido",
                filter=~Q(itens_pedido__pedido__status=Pedido.Status.CANCELADO),
            )
        )
        .order_by("-vendidos", "nome")[:4]
    )
    categorias = Categoria.objects.filter(produtos__ativo=True).distinct()

    pedido_ativo = None
    if request.user.is_authenticated:
        pedido_ativo = (
            Pedido.objects.filter(
                usuario=request.user,
                status__in=[
                    Pedido.Status.PENDENTE,
                    Pedido.Status.EM_PREPARACAO,
                    Pedido.Status.PRONTO,
                ],
            )
            .order_by("-data")
            .first()
        )

    return render(
        request,
        "core/home.html",
        {
            "destaques": destaques,
            "categorias": categorias,
            "pedido_ativo": pedido_ativo,
        },
    )
