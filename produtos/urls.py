from django.urls import path

from . import views

app_name = 'produtos'

urlpatterns = [
    path('cardapio/', views.cardapio, name='cardapio'),
    path('produto/<int:pk>/', views.detalhe, name='detalhe'),

    # Área da cantina
    path('painel/cardapio/', views.gerenciar, name='gerenciar'),
    path('painel/cardapio/novo/', views.criar, name='criar'),
    path('painel/cardapio/<int:pk>/editar/', views.editar, name='editar'),
    path('painel/cardapio/<int:pk>/remover/', views.remover, name='remover'),
]
