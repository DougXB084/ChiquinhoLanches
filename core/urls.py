
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("cardapio/", views.cardapio, name="cardapio"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path("meus-pedidos/", views.meus_pedidos, name="meus_pedidos"),
    path("painel-cantina/", views.painel_cantina, name="painel_cantina"),
]
