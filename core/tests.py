from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from pedidos import services

from .models import (
    Carrinho,
    Categoria,
    Ingrediente,
    ItemCarrinho,
    Pedido,
    PerfilUsuario,
    Produto,
)

# Criado pelo chat para testar o site, sem a necessidade de adicionar produtos um a um

User = get_user_model()


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nome="Lanches")
        cls.pao = Ingrediente.objects.create(nome="Pão")
        cls.carne = Ingrediente.objects.create(nome="Carne")
        cls.hamburguer = Produto.objects.create(
            categoria=cls.categoria, nome="Hambúrguer", preco=Decimal("12.00"), estoque=5
        )
        cls.hamburguer.ingredientes.set([cls.pao, cls.carne])
        cls.suco = Produto.objects.create(
            categoria=cls.categoria, nome="Suco", preco=Decimal("5.00"), estoque=2
        )
        cls.aluno = User.objects.create_user("aluno", password="senha-forte-123", first_name="Ana")
        cls.outro = User.objects.create_user("outro", password="senha-forte-123")
        cls.cantineiro = User.objects.create_user("cantina", password="senha-forte-123")
        PerfilUsuario.objects.filter(usuario=cls.cantineiro).update(
            tipo=PerfilUsuario.Tipo.FUNCIONARIO, matricula="F001"
        )
        PerfilUsuario.objects.filter(usuario=cls.aluno).update(
            matricula="2024001", cpf="52998224725"
        )

    def entrar(self, usuario):
        self.client.force_login(usuario)


class ModelsTests(BaseTestCase):
    def test_usuario_novo_ganha_perfil_e_carrinho(self):
        self.assertTrue(PerfilUsuario.objects.filter(usuario=self.aluno).exists())
        self.assertTrue(Carrinho.objects.filter(usuario=self.aluno).exists())

    def test_total_do_carrinho(self):
        carrinho = self.aluno.carrinho
        ItemCarrinho.objects.create(carrinho=carrinho, produto=self.hamburguer, quantidade=2)
        ItemCarrinho.objects.create(carrinho=carrinho, produto=self.suco, quantidade=1)
        self.assertEqual(carrinho.total, Decimal("29.00"))
        self.assertEqual(carrinho.quantidade_total, 3)

    def test_historico_registra_cada_mudanca_de_status(self):
        pedido = Pedido.objects.create(usuario=self.aluno)
        pedido.status = Pedido.Status.EM_PREPARACAO
        pedido.save()
        pedido.save()  # sem mudança, não duplica
        status = [h.status for h in pedido.historico.all()]
        self.assertEqual(status, ["em_preparacao", "pendente"])

    def test_cancelar_pelo_admin_devolve_estoque(self):
        ItemCarrinho.objects.create(
            carrinho=self.aluno.carrinho, produto=self.hamburguer, quantidade=2
        )
        pedido = services.finalizar_pedido(self.aluno)
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 3)

        pedido = Pedido.objects.get(pk=pedido.pk)
        pedido.status = Pedido.Status.CANCELADO
        pedido.save()
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 5)


class PaginasPublicasTests(BaseTestCase):
    def test_paginas_abrem(self):
        for nome, args in [
            ("core:home", []),
            ("produtos:cardapio", []),
            ("produtos:detalhe", [self.hamburguer.pk]),
            ("usuarios:login", []),
            ("usuarios:cadastro", []),
        ]:
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome, args=args))
                self.assertEqual(resposta.status_code, 200)

    def test_detalhe_mostra_ingredientes(self):
        resposta = self.client.get(reverse("produtos:detalhe", args=[self.hamburguer.pk]))
        self.assertContains(resposta, "Pão")
        self.assertContains(resposta, "Carne")

    def test_cardapio_filtra_por_busca_e_categoria(self):
        resposta = self.client.get(reverse("produtos:cardapio"), {"q": "hambúrguer"})
        self.assertContains(resposta, "Hambúrguer")
        self.assertNotContains(resposta, "Suco")
        resposta = self.client.get(reverse("produtos:cardapio"), {"q": "carne"})
        self.assertContains(resposta, "Hambúrguer")

    def test_produto_inativo_some_do_cardapio(self):
        self.suco.ativo = False
        self.suco.save()
        resposta = self.client.get(reverse("produtos:cardapio"))
        self.assertNotContains(resposta, "Suco")
        resposta = self.client.get(reverse("produtos:detalhe", args=[self.suco.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_paginas_privadas_redirecionam_para_login(self):
        for nome in ["usuarios:perfil", "pedidos:carrinho", "pedidos:meus_pedidos", "pedidos:painel"]:
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn(reverse("usuarios:login"), resposta["Location"])


class UsuariosTests(BaseTestCase):
    DADOS = {
        "first_name": "Bia",
        "last_name": "Souza",
        "email": "bia@exemplo.com",
        "matricula": "2024777",
        "cpf": "111.444.777-35",
        "telefone": "",
        "password1": "senha-forte-123",
        "password2": "senha-forte-123",
    }

    def test_cadastro_cria_conta_e_faz_login(self):
        resposta = self.client.post(reverse("usuarios:cadastro"), self.DADOS)
        self.assertRedirects(resposta, reverse("produtos:cardapio"))
        usuario = User.objects.get(username="2024777")
        self.assertEqual(usuario.perfil.matricula, "2024777")
        self.assertEqual(usuario.perfil.cpf, "11144477735")
        self.assertEqual(usuario.perfil.cpf_formatado, "111.444.777-35")
        self.assertEqual(usuario.perfil.tipo, PerfilUsuario.Tipo.ALUNO)
        self.assertEqual(self.client.get(reverse("usuarios:perfil")).status_code, 200)

    def test_cadastro_nao_pede_turma_nem_usuario(self):
        resposta = self.client.get(reverse("usuarios:cadastro"))
        campos = list(resposta.context["form"].fields)
        self.assertEqual(
            campos,
            ["first_name", "last_name", "email", "matricula", "cpf",
             "telefone", "password1", "password2"],
        )

    def test_cadastro_telefone_e_opcional(self):
        dados = {**self.DADOS, "telefone": ""}
        resposta = self.client.post(reverse("usuarios:cadastro"), dados)
        self.assertEqual(resposta.status_code, 302)

    def test_cadastro_rejeita_repetidos_e_cpf_invalido(self):
        casos = [
            ({"email": "ANA@x.com"}, None),
            ({"matricula": "2024001"}, "Esta matrícula já está cadastrada."),
            ({"cpf": "529.982.247-25"}, "Este CPF já está cadastrado."),
            ({"cpf": "111.111.111-11"}, "Informe um CPF válido."),
            ({"cpf": "123.456.789-00"}, "Informe um CPF válido."),
            ({"password2": "outra-senha-123"}, "As senhas não são iguais."),
            ({"password1": "123", "password2": "123"}, "muito curta"),
        ]
        self.aluno.email = "ana@x.com"
        self.aluno.save()
        for alteracao, mensagem in casos:
            with self.subTest(alteracao=alteracao):
                resposta = self.client.post(
                    reverse("usuarios:cadastro"), {**self.DADOS, **alteracao}
                )
                self.assertEqual(resposta.status_code, 200)
                if mensagem:
                    self.assertContains(resposta, mensagem)
        self.assertFalse(User.objects.filter(username="2024777").exists())

    def test_login_com_matricula_e_logout(self):
        resposta = self.client.post(
            reverse("usuarios:login"),
            {"username": "2024001", "password": "senha-forte-123"},
        )
        self.assertRedirects(resposta, reverse("core:home"))
        self.client.post(reverse("usuarios:logout"))
        self.assertEqual(self.client.get(reverse("usuarios:perfil")).status_code, 302)

    def test_login_errado_nao_diz_o_que_falhou(self):
        for usuario in ["2024001", "naoexiste"]:
            resposta = self.client.post(
                reverse("usuarios:login"), {"username": usuario, "password": "errada"}
            )
            self.assertContains(resposta, "Matrícula ou senha incorretos.")

    def test_login_de_conta_sem_matricula_usa_nome_de_usuario(self):
        resposta = self.client.post(
            reverse("usuarios:login"), {"username": "outro", "password": "senha-forte-123"}
        )
        self.assertEqual(resposta.status_code, 302)

    def test_funcionario_cai_no_painel_ao_entrar(self):
        resposta = self.client.post(
            reverse("usuarios:login"), {"username": "F001", "password": "senha-forte-123"}
        )
        self.assertRedirects(resposta, reverse("pedidos:painel"))

    def test_perfil_mostra_dados_sem_aviso_de_aluno(self):
        self.entrar(self.aluno)
        resposta = self.client.get(reverse("usuarios:perfil"))
        self.assertContains(resposta, "2024001")
        self.assertContains(resposta, "529.982.247-25")
        self.assertNotContains(resposta, "Funcionário da cantina")
        self.entrar(self.cantineiro)
        resposta = self.client.get(reverse("usuarios:perfil"))
        self.assertContains(resposta, "Funcionário da cantina")


class AreaDaCantinaTests(BaseTestCase):
    def test_aluno_nao_acessa_areas_da_cantina(self):
        self.entrar(self.aluno)
        for nome, args in [
            ("produtos:gerenciar", []),
            ("produtos:criar", []),
            ("produtos:editar", [self.suco.pk]),
            ("usuarios:cadastro_funcionario", []),
        ]:
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome, args=args)).status_code, 403)
        resposta = self.client.post(reverse("produtos:remover", args=[self.suco.pk]))
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Produto.objects.filter(pk=self.suco.pk).exists())

    def test_funcionario_home_vai_para_o_painel_e_nao_compra(self):
        self.entrar(self.cantineiro)
        self.assertRedirects(self.client.get(reverse("core:home")), reverse("pedidos:painel"))
        resposta = self.client.post(
            reverse("pedidos:carrinho_adicionar", args=[self.suco.pk]), {"quantidade": 1}
        )
        self.assertRedirects(resposta, reverse("produtos:gerenciar"))
        self.assertFalse(ItemCarrinho.objects.exists())
        resposta = self.client.get(reverse("produtos:cardapio"))
        self.assertContains(resposta, "Editar")
        self.assertNotContains(resposta, "Adicionar</button>")

    def test_funcionario_adiciona_item_com_ingredientes_novos(self):
        self.entrar(self.cantineiro)
        resposta = self.client.post(
            reverse("produtos:criar"),
            {
                "nome": "X-Bacon",
                "descricao": "Com bacon crocante",
                "categoria": "",
                "nova_categoria": "Especiais",
                "preco": "18.50",
                "estoque": "10",
                "ativo": "on",
                "ingredientes": [self.pao.pk],
                "novos_ingredientes": "Bacon, carne",
            },
        )
        self.assertRedirects(resposta, reverse("produtos:gerenciar"))
        produto = Produto.objects.get(nome="X-Bacon")
        self.assertEqual(produto.categoria.nome, "Especiais")
        self.assertEqual(produto.preco, Decimal("18.50"))
        # "carne" já existia (sem diferenciar maiúsculas): não duplica
        self.assertEqual(
            sorted(produto.ingredientes.values_list("nome", flat=True)),
            ["Bacon", "Carne", "Pão"],
        )
        self.assertEqual(Ingrediente.objects.filter(nome__iexact="carne").count(), 1)

    def test_formulario_valida_preco_e_categoria(self):
        self.entrar(self.cantineiro)
        resposta = self.client.post(
            reverse("produtos:criar"),
            {"nome": "Teste", "preco": "0", "estoque": "1", "categoria": ""},
        )
        self.assertContains(resposta, "maior que zero")
        self.assertContains(resposta, "Escolha uma categoria ou crie uma nova.")
        self.assertFalse(Produto.objects.filter(nome="Teste").exists())

    def test_funcionario_edita_preco_descricao_e_status_do_item(self):
        self.entrar(self.cantineiro)
        self.client.post(
            reverse("produtos:editar", args=[self.suco.pk]),
            {
                "nome": "Suco", "descricao": "Natural",
                "categoria": self.categoria.pk, "preco": "6.00", "estoque": "2",
            },  # sem "ativo": desmarcado
        )
        self.suco.refresh_from_db()
        self.assertEqual(self.suco.preco, Decimal("6.00"))
        self.assertEqual(self.suco.descricao, "Natural")
        self.assertFalse(self.suco.ativo)

    def test_remover_apaga_ou_desativa_se_ja_foi_pedido(self):
        self.entrar(self.cantineiro)
        self.client.post(reverse("produtos:remover", args=[self.suco.pk]))
        self.assertFalse(Produto.objects.filter(pk=self.suco.pk).exists())

        ItemCarrinho.objects.create(
            carrinho=self.aluno.carrinho, produto=self.hamburguer, quantidade=1
        )
        services.finalizar_pedido(self.aluno)
        resposta = self.client.post(
            reverse("produtos:remover", args=[self.hamburguer.pk]), follow=True
        )
        self.hamburguer.refresh_from_db()
        self.assertFalse(self.hamburguer.ativo)
        self.assertContains(resposta, "foi desativado")

    def test_funcionario_cadastra_outro_funcionario_que_consegue_entrar(self):
        self.entrar(self.cantineiro)
        dados = {**UsuariosTests.DADOS, "matricula": "F002"}
        resposta = self.client.post(reverse("usuarios:cadastro_funcionario"), dados)
        self.assertRedirects(resposta, reverse("pedidos:painel"))
        novo = User.objects.get(username="F002")
        self.assertTrue(novo.perfil.eh_funcionario)

        self.client.logout()
        resposta = self.client.post(
            reverse("usuarios:login"), {"username": "F002", "password": "senha-forte-123"}
        )
        self.assertRedirects(resposta, reverse("pedidos:painel"))


class CarrinhoETests(BaseTestCase):
    def setUp(self):
        self.entrar(self.aluno)

    def adicionar(self, produto, quantidade=1):
        return self.client.post(
            reverse("pedidos:carrinho_adicionar", args=[produto.pk]),
            {"quantidade": quantidade},
        )

    def test_adicionar_soma_quantidades_e_respeita_estoque(self):
        self.adicionar(self.suco, 1)
        self.adicionar(self.suco, 5)  # só há 2
        item = ItemCarrinho.objects.get(carrinho=self.aluno.carrinho, produto=self.suco)
        self.assertEqual(item.quantidade, 2)

    def test_atualizar_e_remover(self):
        self.adicionar(self.hamburguer, 1)
        item = ItemCarrinho.objects.get()
        self.client.post(reverse("pedidos:carrinho_atualizar", args=[item.pk]), {"quantidade": 3})
        item.refresh_from_db()
        self.assertEqual(item.quantidade, 3)
        self.client.post(reverse("pedidos:carrinho_atualizar", args=[item.pk]), {"quantidade": 0})
        self.assertFalse(ItemCarrinho.objects.exists())

    def test_nao_mexe_no_carrinho_de_outro_usuario(self):
        ItemCarrinho.objects.create(
            carrinho=self.outro.carrinho, produto=self.suco, quantidade=1
        )
        item = ItemCarrinho.objects.get()
        resposta = self.client.post(reverse("pedidos:carrinho_remover", args=[item.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_pagina_do_carrinho(self):
        self.adicionar(self.hamburguer, 2)
        resposta = self.client.get(reverse("pedidos:carrinho"))
        self.assertContains(resposta, "Hambúrguer")
        self.assertContains(resposta, "24,00")

    def test_finalizar_pedido(self):
        self.adicionar(self.hamburguer, 2)
        self.adicionar(self.suco, 1)
        resposta = self.client.post(
            reverse("pedidos:finalizar"), {"observacao": "sem cebola"}
        )
        pedido = Pedido.objects.get()
        self.assertRedirects(resposta, reverse("pedidos:status", args=[pedido.pk]))
        self.assertEqual(pedido.total, Decimal("29.00"))
        self.assertEqual(pedido.observacao, "sem cebola")
        self.assertEqual(pedido.itens.count(), 2)
        self.assertFalse(self.aluno.carrinho.itens.exists())
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 3)

    def test_preco_do_pedido_nao_muda_com_o_cardapio(self):
        self.adicionar(self.hamburguer, 1)
        self.client.post(reverse("pedidos:finalizar"))
        self.hamburguer.preco = Decimal("20.00")
        self.hamburguer.save()
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.itens.get().preco, Decimal("12.00"))
        self.assertEqual(pedido.total, Decimal("12.00"))

    def test_finalizar_sem_estoque_suficiente(self):
        self.adicionar(self.suco, 2)
        Produto.objects.filter(pk=self.suco.pk).update(estoque=1)
        resposta = self.client.post(reverse("pedidos:finalizar"), follow=True)
        self.assertFalse(Pedido.objects.exists())
        self.assertContains(resposta, "restam apenas 1")
        self.assertTrue(self.aluno.carrinho.itens.exists())

    def test_finalizar_carrinho_vazio(self):
        resposta = self.client.post(reverse("pedidos:finalizar"), follow=True)
        self.assertFalse(Pedido.objects.exists())
        self.assertContains(resposta, "carrinho está vazio")


class PedidosTests(BaseTestCase):
    def criar_pedido(self, usuario=None, quantidade=2):
        usuario = usuario or self.aluno
        ItemCarrinho.objects.create(
            carrinho=usuario.carrinho, produto=self.hamburguer, quantidade=quantidade
        )
        return services.finalizar_pedido(usuario)

    def test_meus_pedidos_lista_so_os_do_usuario(self):
        meu = self.criar_pedido(self.aluno)
        alheio = self.criar_pedido(self.outro, 1)
        self.entrar(self.aluno)
        resposta = self.client.get(reverse("pedidos:meus_pedidos"))
        self.assertContains(resposta, f"Pedido #{meu.pk}")
        self.assertNotContains(resposta, f"Pedido #{alheio.pk}")

    def test_status_so_para_dono_ou_funcionario(self):
        pedido = self.criar_pedido()
        url = reverse("pedidos:status", args=[pedido.pk])
        self.entrar(self.outro)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.entrar(self.cantineiro)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.entrar(self.aluno)
        resposta = self.client.get(url)
        self.assertContains(resposta, "Pendente")
        self.assertContains(resposta, "Cancelar pedido")

    def test_status_json(self):
        pedido = self.criar_pedido()
        self.entrar(self.aluno)
        dados = self.client.get(reverse("pedidos:status_json", args=[pedido.pk])).json()
        self.assertEqual(dados["status"], "pendente")

    def test_cliente_cancela_pedido_pendente_e_estoque_volta(self):
        pedido = self.criar_pedido(quantidade=2)
        self.entrar(self.aluno)
        self.client.post(reverse("pedidos:cancelar", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.CANCELADO)
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 5)
        resposta = self.client.get(reverse("pedidos:status", args=[pedido.pk]))
        self.assertContains(resposta, "Este pedido foi cancelado.")

    def test_cliente_nao_cancela_pedido_em_preparo(self):
        pedido = self.criar_pedido()
        pedido.status = Pedido.Status.EM_PREPARACAO
        pedido.save()
        self.entrar(self.aluno)
        self.client.post(reverse("pedidos:cancelar", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.EM_PREPARACAO)

    def test_cliente_nao_cancela_pedido_de_outro(self):
        pedido = self.criar_pedido()
        self.entrar(self.outro)
        resposta = self.client.post(reverse("pedidos:cancelar", args=[pedido.pk]))
        self.assertEqual(resposta.status_code, 404)


class PainelTests(BaseTestCase):
    def criar_pedido(self):
        ItemCarrinho.objects.create(
            carrinho=self.aluno.carrinho, produto=self.hamburguer, quantidade=1
        )
        return services.finalizar_pedido(self.aluno)

    def test_aluno_nao_acessa_painel(self):
        self.entrar(self.aluno)
        self.assertEqual(self.client.get(reverse("pedidos:painel")).status_code, 403)
        pedido = self.criar_pedido()
        resposta = self.client.post(reverse("pedidos:painel_avancar", args=[pedido.pk]))
        self.assertEqual(resposta.status_code, 403)

    def test_funcionario_ve_pedidos_e_avanca_status(self):
        pedido = self.criar_pedido()
        self.entrar(self.cantineiro)
        resposta = self.client.get(reverse("pedidos:painel"))
        self.assertContains(resposta, f"Pedido #{pedido.pk}")

        esperado = ["em_preparacao", "pronto", "entregue"]
        for status in esperado:
            self.client.post(reverse("pedidos:painel_avancar", args=[pedido.pk]))
            pedido.refresh_from_db()
            self.assertEqual(pedido.status, status)

        # Entregue não tem próxima etapa e sai da fila.
        self.client.post(reverse("pedidos:painel_avancar", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "entregue")
        resposta = self.client.get(reverse("pedidos:painel"))
        na_fila = [p for c in resposta.context["colunas"] for p in c["pedidos"]]
        self.assertEqual(na_fila, [])

    def test_cancelamento_da_cantina_exige_justificativa(self):
        pedido = self.criar_pedido()
        self.entrar(self.cantineiro)
        for justificativa in ["", "   ", "abc"]:
            self.client.post(
                reverse("pedidos:painel_cancelar", args=[pedido.pk]),
                {"justificativa": justificativa},
            )
            pedido.refresh_from_db()
            self.assertEqual(pedido.status, Pedido.Status.PENDENTE)
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 4)

    def test_funcionario_cancela_devolve_estoque_e_aluno_ve_justificativa(self):
        pedido = self.criar_pedido()
        self.entrar(self.cantineiro)
        resposta = self.client.post(
            reverse("pedidos:painel_cancelar", args=[pedido.pk]),
            {"justificativa": "Acabou o pão"},
            follow=True,
        )
        self.assertContains(resposta, "reembolso foi feito")
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.CANCELADO)
        self.assertEqual(pedido.cancelado_por, self.cantineiro)
        self.assertTrue(pedido.reembolsado)
        self.hamburguer.refresh_from_db()
        self.assertEqual(self.hamburguer.estoque, 5)

        self.entrar(self.aluno)
        resposta = self.client.get(reverse("pedidos:status", args=[pedido.pk]))
        self.assertContains(resposta, "cancelado pela cantina")
        self.assertContains(resposta, "Acabou o pão")
        self.assertContains(resposta, "O reembolso de R$ 12,00 foi feito com o cancelamento.")
        resposta = self.client.get(reverse("pedidos:meus_pedidos"))
        self.assertContains(resposta, "Acabou o pão")
        self.assertContains(resposta, "Reembolso feito")

    def test_cancelamento_pelo_aluno_nao_mostra_reembolso_da_cantina(self):
        pedido = self.criar_pedido()
        self.entrar(self.aluno)
        self.client.post(reverse("pedidos:cancelar", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertFalse(pedido.reembolsado)
        self.assertFalse(pedido.cancelado_pela_cantina)
        resposta = self.client.get(reverse("pedidos:status", args=[pedido.pk]))
        self.assertNotContains(resposta, "pela cantina")

    def test_painel_mostra_matricula_do_aluno(self):
        self.criar_pedido()
        self.entrar(self.cantineiro)
        resposta = self.client.get(reverse("pedidos:painel"))
        self.assertContains(resposta, "Matrícula 2024001")
        self.assertContains(resposta, "•••.982.247-••")

    def test_staff_do_admin_tambem_acessa(self):
        admin = User.objects.create_user("chefe", password="senha-forte-123", is_staff=True)
        self.entrar(admin)
        self.assertEqual(self.client.get(reverse("pedidos:painel")).status_code, 200)

    def test_timeline_do_pedido_mostra_andamento(self):
        pedido = self.criar_pedido()
        pedido.status = Pedido.Status.PRONTO
        pedido.save()
        self.entrar(self.aluno)
        resposta = self.client.get(reverse("pedidos:status", args=[pedido.pk]))
        self.assertContains(resposta, "Seu pedido está pronto!")
        situacoes = [e["situacao"] for e in resposta.context["etapas"]]
        self.assertEqual(situacoes, ["feita", "feita", "atual", "futura"])
