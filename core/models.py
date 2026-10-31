
# models.py

from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    class Tipo(models.TextChoices):
        ALUNO = "aluno", "Aluno"
        FUNCIONARIO = "funcionario", "Funcionário"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.ALUNO,
    )

    def __str__(self):
        return f"{self.usuario} - {self.get_tipo_display()}"


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome


class Produto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="produtos",
    )
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_PREPARACAO = "em_preparacao", "Em preparação"
        PRONTO = "pronto", "Pronto"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    data = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="itens_pedido",
    )
    quantidade = models.PositiveIntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "produto"],
                name="item_produto_unico_por_pedido",
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0),
                name="item_quantidade_maior_que_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} - Pedido #{self.pedido_id}"

    @property
    def subtotal(self):
        return self.quantidade * self.preco
