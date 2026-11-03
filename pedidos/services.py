from django.db import transaction
from django.db.models import F

from core.models import Carrinho, ItemPedido, Pedido, Produto


class PedidoInvalido(Exception):
    def __init__(self, mensagens):
        self.mensagens = mensagens if isinstance(mensagens, list) else [mensagens]
        super().__init__(" ".join(self.mensagens))


def obter_carrinho(usuario):
    carrinho, _ = Carrinho.objects.get_or_create(usuario=usuario)
    return carrinho


@transaction.atomic
def finalizar_pedido(usuario, observacao=""):
    carrinho = obter_carrinho(usuario)
    itens = list(carrinho.itens.select_related("produto"))
    if not itens:
        raise PedidoInvalido("Seu carrinho está vazio.")

    produtos = {
        p.pk: p
        for p in Produto.objects.select_for_update().filter(
            pk__in=[i.produto_id for i in itens]
        )
    }

    problemas = []
    for item in itens:
        produto = produtos[item.produto_id]
        if not produto.ativo or produto.estoque <= 0:
            problemas.append(f"{produto.nome} não está mais disponível.")
        elif item.quantidade > produto.estoque:
            problemas.append(
                f"{produto.nome}: restam apenas {produto.estoque} unidade(s)."
            )
    if problemas:
        raise PedidoInvalido(problemas)

    pedido = Pedido.objects.create(usuario=usuario, observacao=observacao.strip()[:250])
    for item in itens:
        produto = produtos[item.produto_id]
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=item.quantidade,
            preco=produto.preco,
        )
        Produto.objects.filter(pk=produto.pk).update(
            estoque=F("estoque") - item.quantidade
        )

    pedido.recalcular_total()
    pedido.save(update_fields=["total"])
    carrinho.itens.all().delete()
    return pedido


@transaction.atomic
def cancelar_pedido(pedido, por=None, justificativa=""):
    """Cancela o pedido (o estoque volta pelo próprio Pedido.save).

    Quando quem cancela é a cantina (outra pessoa que não o dono do pedido),
    a justificativa é obrigatória, fica visível para o aluno e o pedido é
    marcado como reembolsado.
    """
    if pedido.status in (Pedido.Status.ENTREGUE, Pedido.Status.CANCELADO):
        raise PedidoInvalido("Este pedido não pode mais ser cancelado.")

    pela_cantina = por is not None and por.pk != pedido.usuario_id
    if pela_cantina:
        justificativa = (justificativa or "").strip()
        if len(justificativa) < 5:
            raise PedidoInvalido(
                "Escreva a justificativa do cancelamento (mínimo de 5 caracteres)."
            )
        pedido.justificativa_cancelamento = justificativa[:500]
        pedido.reembolsado = True

    pedido.cancelado_por = por
    pedido.status = Pedido.Status.CANCELADO
    pedido.save()
    return pedido
