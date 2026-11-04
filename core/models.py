# Informações para apresentação, no caso de esquecer :)
#
# Todos os models do sistema ficam neste app (core). Os apps usuarios, produtos
# e pedidos cuidam apenas das telas (views, urls e templates) de cada área.

# Relações principais:
#   User 1─1 Perfil
#   User 1─1 Carrinho 1─N ItemCarrinho N─1 Produto
#   User 1─N Pedido 1─N ItemPedido N─1 Produto
#   Pedido 1─N HistoricoStatus
#   Categoria 1─N Produto N─N Ingrediente

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Sum

from .validators import somente_digitos, validar_cpf


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
    # A cantina identifica o aluno pela matrícula ou pelo CPF.
    # Os campos aceitam nulo para não quebrar usuários antigos (ex.: superusuário).
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    cpf = models.CharField(
        "CPF",
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_cpf],
        help_text="Pode digitar com pontos e traço; é guardado só com números.",
    )
    telefone = models.CharField(max_length=20, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "perfil de usuário"
        verbose_name_plural = "perfis de usuários"

    def __str__(self):
        return f"{self.usuario} - {self.get_tipo_display()}"

    @property
    def eh_funcionario(self):
        return self.tipo == self.Tipo.FUNCIONARIO

    @property
    def cpf_formatado(self):
        c = self.cpf or ""
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else c

    @property
    def cpf_mascarado(self):
        c = self.cpf or ""
        return f"•••.{c[3:6]}.{c[6:9]}-••" if len(c) == 11 else ""

    def save(self, *args, **kwargs):
        if self.cpf:
            self.cpf = somente_digitos(self.cpf)
        if self.matricula:
            self.matricula = self.matricula.strip()
        super().save(*args, **kwargs)


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveSmallIntegerField(
        default=0,
        help_text="Define a posição da categoria no cardápio (menor aparece primeiro).",
    )

    class Meta:
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Ingrediente(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]

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
    imagem = models.ImageField(upload_to="produtos/", blank=True)
    ingredientes = models.ManyToManyField(
        Ingrediente,
        blank=True,
        related_name="produtos",
    )

    class Meta:
        ordering = ["categoria__ordem", "nome"]

    def __str__(self):
        return self.nome

    @property
    def disponivel(self):
        return self.ativo and self.estoque > 0


class Carrinho(models.Model):
    """Carrinho persistente: cada usuário tem exatamente um."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carrinho",
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrinho de {self.usuario}"

    @property
    def total(self):
        resultado = self.itens.aggregate(
            total=Sum(F("quantidade") * F("produto__preco"))
        )["total"]
        return resultado or Decimal("0.00")

    @property
    def quantidade_total(self):
        return self.itens.aggregate(q=Sum("quantidade"))["q"] or 0


class ItemCarrinho(models.Model):
    carrinho = models.ForeignKey(
        Carrinho,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="itens_carrinho",
    )
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["carrinho", "produto"],
                name="item_carrinho_produto_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0),
                name="item_carrinho_quantidade_maior_que_zero",
            ),
        ]

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"

    @property
    def subtotal(self):
        return self.quantidade * self.produto.preco


class Pedido(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_PREPARACAO = "em_preparacao", "Em preparação"
        PRONTO = "pronto", "Pronto"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"

    # Sequência normal de um pedido (o cancelamento fica fora dela).
    FLUXO = [
        Status.PENDENTE,
        Status.EM_PREPARACAO,
        Status.PRONTO,
        Status.ENTREGUE,
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    data = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
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
    observacao = models.CharField(
        max_length=250,
        blank=True,
        help_text="Ex.: sem cebola, cortar ao meio.",
    )
    # Cancelamento: quem cancelou, por quê e se o valor foi devolvido.
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_cancelados",
    )
    justificativa_cancelamento = models.TextField(
        blank=True,
        help_text="Motivo informado pela cantina; o aluno vê no pedido.",
    )
    reembolsado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-data"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status_original = self.status

    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario}"

    @property
    def proximo_status(self):
        """Próximo status do fluxo normal, ou None se não houver."""
        if self.status not in self.FLUXO:
            return None
        posicao = self.FLUXO.index(self.status)
        if posicao + 1 >= len(self.FLUXO):
            return None
        return self.FLUXO[posicao + 1]

    @property
    def proximo_status_rotulo(self):
        proximo = self.proximo_status
        return self.Status(proximo).label if proximo else ""

    @property
    def em_andamento(self):
        return self.status in (
            self.Status.PENDENTE,
            self.Status.EM_PREPARACAO,
            self.Status.PRONTO,
        )

    @property
    def cancelado_pela_cantina(self):
        return (
            self.status == self.Status.CANCELADO
            and self.cancelado_por_id is not None
            and self.cancelado_por_id != self.usuario_id
        )

    @property
    def pode_cancelar(self):
        return self.status == self.Status.PENDENTE

    def recalcular_total(self):
        resultado = self.itens.aggregate(
            total=Sum(F("quantidade") * F("preco"))
        )["total"]
        self.total = resultado or Decimal("0.00")
        return self.total

    def save(self, *args, **kwargs):
        criado_agora = self._state.adding
        super().save(*args, **kwargs)

        # Cancelamento devolve os itens ao estoque (vale também para o admin).
        if (
            not criado_agora
            and self.status == self.Status.CANCELADO
            and self._status_original != self.Status.CANCELADO
        ):
            for item in self.itens.select_related("produto"):
                Produto.objects.filter(pk=item.produto_id).update(
                    estoque=F("estoque") + item.quantidade
                )

        # Registra a mudança de status na linha do tempo.
        ultimo = self.historico.first()
        if ultimo is None or ultimo.status != self.status:
            HistoricoStatus.objects.create(pedido=self, status=self.status)

        self._status_original = self.status


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
    # Preço unitário no momento da compra (não muda se o cardápio mudar).
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


class HistoricoStatus(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="historico",
    )
    status = models.CharField(max_length=20, choices=Pedido.Status.choices)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]
        verbose_name = "histórico de status"
        verbose_name_plural = "histórico de status"

    def __str__(self):
        return f"Pedido #{self.pedido_id}: {self.get_status_display()}"
