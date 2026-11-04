# admin.py
#
# É aqui que a cantina edita o cardápio (categorias, ingredientes, produtos,
# preços e estoque) e também pode acompanhar os pedidos.

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (
    Carrinho,
    Categoria,
    HistoricoStatus,
    Ingrediente,
    ItemCarrinho,
    ItemPedido,
    Pedido,
    PerfilUsuario,
    Produto,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo", "matricula", "cpf", "telefone")
    list_filter = ("tipo",)
    search_fields = ("usuario__username", "usuario__email", "matricula", "cpf")


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    fk_name = "usuario"


class UsuarioAdmin(UserAdmin):
    """Usuário com matrícula, CPF e tipo (aluno/funcionário) na mesma tela."""

    inlines = [PerfilUsuarioInline]

    def get_inline_instances(self, request, obj=None):
        # O perfil nasce sozinho (signal) ao criar o usuário; por isso o bloco
        # só aparece na edição, evitando criar dois perfis.
        return super().get_inline_instances(request, obj) if obj else []


User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")
    list_editable = ("ordem",)
    search_fields = ("nome",)


@admin.register(Ingrediente)
class IngredienteAdmin(admin.ModelAdmin):
    search_fields = ("nome",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "estoque", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("nome",)
    list_editable = ("preco", "estoque", "ativo")
    filter_horizontal = ("ingredientes",)


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


class HistoricoStatusInline(admin.TabularInline):
    model = HistoricoStatus
    extra = 0
    can_delete = False
    readonly_fields = ("status", "data")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "data", "status", "total")
    search_fields = ("usuario__username", "usuario__email", "usuario__perfil__matricula")
    readonly_fields = ("data", "atualizado_em")
    list_filter = ("status", "reembolsado", "data")
    inlines = [ItemPedidoInline, HistoricoStatusInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "produto", "quantidade", "preco")
    list_filter = ("produto",)


class ItemCarrinhoInline(admin.TabularInline):
    model = ItemCarrinho
    extra = 0


@admin.register(Carrinho)
class CarrinhoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "atualizado_em")
    search_fields = ("usuario__username",)
    inlines = [ItemCarrinhoInline]
