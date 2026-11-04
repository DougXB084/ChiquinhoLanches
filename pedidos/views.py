from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import ItemCarrinho, Pedido, Produto
from core.permissions import eh_funcionario, funcionario_required

from . import services


def _voltar_para(request, padrao):
    destino = request.POST.get("next", "")
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}
    ):
        return redirect(destino)
    return redirect(padrao)


def _quantidade(valor, padrao=1):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return padrao


# ---------------------------------------------------------------- Carrinho

@login_required
def carrinho(request):
    carrinho_usuario = services.obter_carrinho(request.user)
    itens = carrinho_usuario.itens.select_related("produto__categoria")
    return render(
        request,
        "pedidos/carrinho.html",
        {
            "carrinho": carrinho_usuario,
            "itens": itens,
            "total": carrinho_usuario.total,
            "tem_indisponivel": any(not i.produto.disponivel for i in itens),
        },
    )


@login_required
@require_POST
def carrinho_adicionar(request, produto_id):
    if eh_funcionario(request.user):
        messages.error(request, "A conta da cantina não faz pedidos.")
        return redirect("produtos:gerenciar")

    produto = get_object_or_404(Produto, pk=produto_id, ativo=True)
    quantidade = max(_quantidade(request.POST.get("quantidade")), 1)

    if produto.estoque <= 0:
        messages.error(request, f"{produto.nome} está esgotado.")
        return _voltar_para(request, "produtos:cardapio")

    carrinho_usuario = services.obter_carrinho(request.user)
    item = ItemCarrinho.objects.filter(
        carrinho=carrinho_usuario, produto=produto
    ).first()
    nova = (item.quantidade if item else 0) + quantidade

    if nova > produto.estoque:
        nova = produto.estoque
        messages.info(
            request, f"Só temos {produto.estoque} unidade(s) de {produto.nome}."
        )
    else:
        messages.success(request, f"{produto.nome} foi para o carrinho.")

    if item:
        item.quantidade = nova
        item.save()
    else:
        ItemCarrinho.objects.create(
            carrinho=carrinho_usuario, produto=produto, quantidade=nova
        )
    return _voltar_para(request, "produtos:cardapio")


@login_required
@require_POST
def carrinho_atualizar(request, item_id):
    item = get_object_or_404(
        ItemCarrinho.objects.select_related("produto"),
        pk=item_id,
        carrinho__usuario=request.user,
    )
    quantidade = _quantidade(request.POST.get("quantidade"), item.quantidade)

    if quantidade <= 0:
        item.delete()
        messages.success(request, f"{item.produto.nome} saiu do carrinho.")
        return redirect("pedidos:carrinho")

    if quantidade > item.produto.estoque:
        quantidade = max(item.produto.estoque, 1)
        messages.info(
            request,
            f"Só temos {item.produto.estoque} unidade(s) de {item.produto.nome}.",
        )
    item.quantidade = quantidade
    item.save()
    return redirect("pedidos:carrinho")


@login_required
@require_POST
def carrinho_remover(request, item_id):
    item = get_object_or_404(
        ItemCarrinho.objects.select_related("produto"),
        pk=item_id,
        carrinho__usuario=request.user,
    )
    item.delete()
    messages.success(request, f"{item.produto.nome} saiu do carrinho.")
    return redirect("pedidos:carrinho")


@login_required
@require_POST
def finalizar(request):
    try:
        pedido = services.finalizar_pedido(
            request.user, request.POST.get("observacao", "")
        )
    except services.PedidoInvalido as erro:
        for mensagem in erro.mensagens:
            messages.error(request, mensagem)
        return redirect("pedidos:carrinho")

    messages.success(request, f"Pedido #{pedido.pk} enviado para a cantina!")
    return redirect("pedidos:status", pk=pedido.pk)


# ----------------------------------------------------------- Meus pedidos

@login_required
def meus_pedidos(request):
    pedidos = (
        Pedido.objects.filter(usuario=request.user)
        .prefetch_related("itens__produto")
        .order_by("-data")
    )
    return render(
        request,
        "pedidos/meus_pedidos.html",
        {
            "em_andamento": [p for p in pedidos if p.em_andamento],
            "anteriores": [p for p in pedidos if not p.em_andamento],
            "total_pedidos": len(pedidos),
        },
    )


def _pedido_visivel(request, pk):
    """Dono do pedido ou funcionário da cantina; qualquer outro recebe 404."""
    pedido = get_object_or_404(
        Pedido.objects.select_related("usuario__perfil").prefetch_related(
            "itens__produto", "historico"
        ),
        pk=pk,
    )
    if pedido.usuario_id != request.user.pk and not eh_funcionario(request.user):
        raise Http404
    return pedido


@login_required
def status(request, pk):
    pedido = _pedido_visivel(request, pk)

    historico = {h.status: h.data for h in pedido.historico.all()}
    cancelado = pedido.status == Pedido.Status.CANCELADO

    if cancelado:
        # Mostra só as etapas que o pedido chegou a cumprir, e depois o cancelamento.
        etapas_fluxo = [s for s in Pedido.FLUXO if s in historico]
        posicao_atual = len(Pedido.FLUXO)
    else:
        etapas_fluxo = Pedido.FLUXO
        posicao_atual = Pedido.FLUXO.index(pedido.status)

    etapas = []
    for etapa in etapas_fluxo:
        indice = Pedido.FLUXO.index(etapa)
        if indice < posicao_atual:
            situacao = "feita"
        elif indice == posicao_atual:
            situacao = "atual"
        else:
            situacao = "futura"
        etapas.append(
            {
                "rotulo": Pedido.Status(etapa).label,
                "situacao": situacao,
                "data": historico.get(etapa),
            }
        )
    if cancelado:
        etapas.append(
            {
                "rotulo": Pedido.Status.CANCELADO.label,
                "situacao": "cancelada",
                "data": historico.get(Pedido.Status.CANCELADO),
            }
        )

    return render(
        request,
        "pedidos/status.html",
        {"pedido": pedido, "etapas": etapas},
    )


@login_required
def status_json(request, pk):
    pedido = _pedido_visivel(request, pk)
    return JsonResponse(
        {"status": pedido.status, "rotulo": pedido.get_status_display()}
    )


@login_required
@require_POST
def cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk, usuario=request.user)
    if not pedido.pode_cancelar:
        messages.error(
            request, "A cantina já começou a preparar este pedido e ele não pode ser cancelado."
        )
        return redirect("pedidos:status", pk=pk)
    services.cancelar_pedido(pedido, por=request.user)
    messages.success(request, f"Pedido #{pedido.pk} cancelado.")
    return redirect("pedidos:status", pk=pk)


# --------------------------------------------------------- Painel da cantina

@funcionario_required
def painel(request):
    base = Pedido.objects.select_related("usuario__perfil").prefetch_related(
        "itens__produto"
    )
    colunas = [
        {
            "status": s,
            "titulo": rotulo,
            "pedidos": list(base.filter(status=s).order_by("data")),
        }
        for s, rotulo in (
            (Pedido.Status.PENDENTE, "Pendentes"),
            (Pedido.Status.EM_PREPARACAO, "Em preparação"),
            (Pedido.Status.PRONTO, "Prontos para retirar"),
        )
    ]

    hoje = timezone.localdate()
    do_dia = Pedido.objects.filter(data__date=hoje)
    resumo = {
        "pedidos_hoje": do_dia.exclude(status=Pedido.Status.CANCELADO).count(),
        "em_andamento": sum(len(c["pedidos"]) for c in colunas),
        "entregues_hoje": do_dia.filter(status=Pedido.Status.ENTREGUE).count(),
        "faturamento_hoje": do_dia.filter(status=Pedido.Status.ENTREGUE).aggregate(
            t=Sum("total")
        )["t"]
        or 0,
    }
    return render(request, "pedidos/painel.html", {"colunas": colunas, "resumo": resumo})


@funcionario_required
@require_POST
def painel_avancar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    proximo = pedido.proximo_status
    if proximo is None:
        messages.error(request, f"O pedido #{pedido.pk} não tem próxima etapa.")
    else:
        pedido.status = proximo
        pedido.save()
        messages.success(
            request, f"Pedido #{pedido.pk}: {pedido.get_status_display().lower()}."
        )
    return redirect("pedidos:painel")


@funcionario_required
@require_POST
def painel_cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        services.cancelar_pedido(
            pedido,
            por=request.user,
            justificativa=request.POST.get("justificativa", ""),
        )
    except services.PedidoInvalido as erro:
        messages.error(request, str(erro))
    else:
        messages.success(
            request,
            f"Pedido #{pedido.pk} cancelado. O aluno vai ver a justificativa "
            "e o aviso de que o reembolso foi feito.",
        )
    return redirect("pedidos:painel")
