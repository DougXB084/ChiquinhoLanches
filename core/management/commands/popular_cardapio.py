"""Cria um cardápio de exemplo para testar o sistema.

Uso:  python manage.py popular_cardapio
É seguro rodar mais de uma vez (não duplica nada).
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Categoria, Ingrediente, Produto

CARDAPIO = {
    "Lanches": {
        "ordem": 1,
        "itens": [
            ("Hambúrguer", "Clássico da casa, feito na chapa.", "12.00", 30,
             ["Pão", "Carne", "Queijo", "Cebola"]),
            ("X-Salada", "Hambúrguer com salada fresquinha.", "14.00", 25,
             ["Pão", "Carne", "Queijo", "Alface", "Tomate"]),
            ("Misto quente", "Pão, queijo e presunto na chapa.", "7.00", 40,
             ["Pão", "Queijo", "Presunto"]),
            ("Cachorro-quente", "Salsicha, molho e batata palha.", "8.00", 35,
             ["Pão", "Salsicha", "Molho de tomate", "Batata palha"]),
        ],
    },
    "Salgados": {
        "ordem": 2,
        "itens": [
            ("Coxinha", "Frango cremoso com massa crocante.", "6.00", 50,
             ["Massa", "Frango", "Catupiry"]),
            ("Pastel de queijo", "Frito na hora.", "6.50", 30,
             ["Massa de pastel", "Queijo"]),
            ("Pão de queijo", "Porção com 5 unidades.", "5.00", 60,
             ["Polvilho", "Queijo", "Ovo"]),
        ],
    },
    "Bebidas": {
        "ordem": 3,
        "itens": [
            ("Suco de laranja", "Copo de 300 ml, natural.", "5.00", 40, ["Laranja"]),
            ("Refrigerante lata", "Lata de 350 ml.", "5.50", 48, []),
            ("Água mineral", "Garrafa de 500 ml.", "3.00", 80, []),
        ],
    },
    "Doces": {
        "ordem": 4,
        "itens": [
            ("Brigadeiro", "Tradicional, com granulado.", "3.00", 50,
             ["Leite condensado", "Chocolate", "Granulado"]),
            ("Bolo de cenoura", "Fatia com cobertura de chocolate.", "6.00", 20,
             ["Cenoura", "Farinha", "Ovo", "Chocolate"]),
        ],
    },
}


class Command(BaseCommand):
    help = "Cria categorias, ingredientes e produtos de exemplo."

    def handle(self, *args, **options):
        criados = 0
        for nome_categoria, dados in CARDAPIO.items():
            categoria, _ = Categoria.objects.get_or_create(
                nome=nome_categoria, defaults={"ordem": dados["ordem"]}
            )
            for nome, descricao, preco, estoque, ingredientes in dados["itens"]:
                produto, novo = Produto.objects.get_or_create(
                    categoria=categoria,
                    nome=nome,
                    defaults={
                        "descricao": descricao,
                        "preco": Decimal(preco),
                        "estoque": estoque,
                    },
                )
                if novo:
                    criados += 1
                    for nome_ingrediente in ingredientes:
                        ingrediente, _ = Ingrediente.objects.get_or_create(
                            nome=nome_ingrediente
                        )
                        produto.ingredientes.add(ingrediente)
        self.stdout.write(self.style.SUCCESS(f"{criados} produto(s) criado(s)."))
