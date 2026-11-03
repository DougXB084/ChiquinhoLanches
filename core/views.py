from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from .models import Categoria, Produto, Pedido


def home(request):
    produtos = Produto.objects.filter(ativo=True)[:3]

    return render(request, "core/home.html", {
        "produtos": produtos,
    })


def login_view(request):
    return render(request, "core/login.html")


def cadastro(request):
    return render(request, "core/cadastro.html")


def cardapio(request):
    categorias = Categoria.objects.prefetch_related(
        "produtos"
    ).all()

    produtos = Produto.objects.filter(
        ativo=True,
        estoque__gt=0,
    ).select_related("categoria")

    return render(request, "core/cardapio.html", {
        "categorias": categorias,
        "produtos": produtos,
    })


def carrinho(request):
    return render(request, "core/carrinho.html")


def meus_pedidos(request):
    pedidos = Pedido.objects.filter(
        usuario=request.user
    ).prefetch_related("itens__produto").order_by("-data") if request.user.is_authenticated else []

    return render(request, "core/meus_pedidos.html", {
        "pedidos": pedidos,
    })


@staff_member_required
def painel_cantina(request):
    pedidos = Pedido.objects.all().order_by("-data")[:10]

    return render(request, "core/painel_cantina.html", {
        "pedidos": pedidos,
        "total_pedidos": Pedido.objects.count(),
        "total_produtos": Produto.objects.count(),
    })
