from django.urls import path

from . import views

app_name = 'pedidos'

urlpatterns = [
    # Carrinho
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.carrinho_adicionar, name='carrinho_adicionar'),
    path('carrinho/atualizar/<int:item_id>/', views.carrinho_atualizar, name='carrinho_atualizar'),
    path('carrinho/remover/<int:item_id>/', views.carrinho_remover, name='carrinho_remover'),
    path('carrinho/finalizar/', views.finalizar, name='finalizar'),

    # Pedidos do cliente
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedido/<int:pk>/', views.status, name='status'),
    path('pedido/<int:pk>/status.json', views.status_json, name='status_json'),
    path('pedido/<int:pk>/cancelar/', views.cancelar, name='cancelar'),

    # Painel da cantina
    path('painel/', views.painel, name='painel'),
    path('painel/pedido/<int:pk>/avancar/', views.painel_avancar, name='painel_avancar'),
    path('painel/pedido/<int:pk>/cancelar/', views.painel_cancelar, name='painel_cancelar'),
]
