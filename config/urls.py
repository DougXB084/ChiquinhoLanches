"""
URL configuration for config project.

Cada app define as próprias rotas, e todas ficam na raiz do site:

    core       /                     home
    usuarios   /login/ /cadastro/ /perfil/ /sair/
    produtos   /cardapio/ /produto/<id>/
    pedidos    /carrinho/ /meus-pedidos/ /pedido/<id>/ /painel/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('usuarios.urls')),
    path('', include('produtos.urls')),
    path('', include('pedidos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
