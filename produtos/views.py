from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Categoria, Produto
from core.permissions import funcionario_required

from .forms import ProdutoForm


def cardapio(request):
    categorias = Categoria.objects.filter(produtos__ativo=True).distinct()
    produtos = Produto.objects.filter(ativo=True).select_related("categoria")

    categoria_atual = None
    categoria_id = request.GET.get("categoria", "")
    if categoria_id.isdigit():
        categoria_atual = categorias.filter(pk=int(categoria_id)).first()
        if categoria_atual:
            produtos = produtos.filter(categoria=categoria_atual)

    busca = request.GET.get("q", "").strip()
    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) | Q(ingredientes__nome__icontains=busca)
        ).distinct()

    return render(
        request,
        "produtos/cardapio.html",
        {
            "produtos": produtos,
            "categorias": categorias,
            "categoria_atual": categoria_atual,
            "busca": busca,
        },
    )


def detalhe(request, pk):
    produto = get_object_or_404(
        Produto.objects.select_related("categoria").prefetch_related("ingredientes"),
        pk=pk,
        ativo=True,
    )
    relacionados = (
        Produto.objects.filter(categoria=produto.categoria, ativo=True, estoque__gt=0)
        .exclude(pk=produto.pk)[:3]
    )
    return render(
        request,
        "produtos/detalhe.html",
        {"produto": produto, "relacionados": relacionados},
    )


# ----------------------------------------------- Área da cantina (cardápio)

@funcionario_required
def gerenciar(request):
    produtos = Produto.objects.select_related("categoria").order_by(
        "categoria__ordem", "categoria__nome", "nome"
    )
    return render(request, "produtos/gerenciar.html", {"produtos": produtos})


def _formulario_produto(request, produto=None):
    form = ProdutoForm(
        request.POST or None, request.FILES or None, instance=produto
    )
    if request.method == "POST" and form.is_valid():
        salvo = form.save()
        messages.success(
            request,
            f"{salvo.nome} foi {'atualizado' if produto else 'adicionado ao cardápio'}.",
        )
        return redirect("produtos:gerenciar")
    return render(
        request, "produtos/produto_form.html", {"form": form, "produto": produto}
    )


@funcionario_required
def criar(request):
    return _formulario_produto(request)


@funcionario_required
def editar(request, pk):
    return _formulario_produto(request, get_object_or_404(Produto, pk=pk))


@funcionario_required
@require_POST
def remover(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    nome = produto.nome
    try:
        produto.delete()
    except ProtectedError:
        # Itens que já aparecem em pedidos não podem sumir do histórico.
        produto.ativo = False
        produto.save(update_fields=["ativo"])
        messages.info(
            request,
            f"{nome} já aparece em pedidos e não pode ser apagado. "
            "Ele foi desativado e saiu do cardápio.",
        )
    else:
        messages.success(request, f"{nome} foi removido do cardápio.")
    return redirect("produtos:gerenciar")
