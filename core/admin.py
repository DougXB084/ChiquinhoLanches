
# admin.py

from django.contrib import admin
from .models import (
    PerfilUsuario,
    Categoria,
    Produto,
    Pedido,
    ItemPedido,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo")
    list_filter = ("tipo",)
    search_fields = ("usuario__username", "usuario__email")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "estoque", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("nome",)
    list_editable = ("preco", "estoque", "ativo")


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "data", "status", "total")
    list_filter = ("status", "data")
    search_fields = ("usuario__username", "usuario__email")
    readonly_fields = ("data",)
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "produto", "quantidade", "preco")
    list_filter = ("produto",)
