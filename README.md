# 🍔 Chiquinho Lanches

Sistema web de **cantina infantil/escolar** desenvolvido em **Django**. Permite que alunos consultem o cardápio, montem um carrinho, façam pedidos e acompanhem cada etapa, enquanto os funcionários da cantina gerenciam o cardápio e o andamento dos pedidos em um painel próprio.

> Projeto Integrador. A especificação completa (requisitos funcionais e diagrama de casos de uso) está no documento *Requisitos Funcionais e Casos de Uso*.

---

## 📑 Sumário

- [Funcionalidades](#-funcionalidades)
- [Perfis de usuário](#-perfis-de-usuário)
- [Tecnologias](#-tecnologias)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Modelo de dados](#-modelo-de-dados)
- [Rotas](#-rotas)
- [Regras de negócio](#-regras-de-negócio)
- [Como executar](#-como-executar)
- [Dados de exemplo](#-dados-de-exemplo)
- [Testes](#-testes)
- [Requisitos funcionais](#-requisitos-funcionais)
- [Observações para produção](#-observações-para-produção)
- [Licença](#-licença)

---

## ✨ Funcionalidades

**Para qualquer visitante**
- Ver a página inicial e o cardápio (apenas produtos ativos, agrupados por categoria).
- Pesquisar produtos por **nome** ou **ingrediente** e filtrar por **categoria**.
- Ver os detalhes de um produto: descrição, preço, imagem, categoria e ingredientes.
- Criar uma conta de aluno.

**Para o aluno**
- Entrar com **matrícula e senha** e consultar o perfil com resumo dos pedidos.
- Adicionar produtos ao carrinho, alterar quantidades e remover itens (limitado ao estoque).
- Finalizar o pedido, com campo de observação (ex.: "sem cebola").
- Acompanhar o pedido em uma linha do tempo de status.
- Cancelar o pedido enquanto ele estiver **pendente**.
- Ver a justificativa e o aviso de reembolso quando a cantina cancelar um pedido.

**Para o funcionário da cantina**
- Acompanhar o **painel de pedidos** (pendentes, em preparação e prontos para retirada) com resumo do dia: pedidos, em andamento, entregues e faturamento.
- Avançar o status do pedido: *Pendente → Em preparação → Pronto → Entregue*.
- Cancelar pedidos com **justificativa obrigatória** (o pedido é marcado como reembolsado).
- Cadastrar, editar e remover produtos do cardápio (com categoria, estoque, ingredientes e imagem).
- Cadastrar outros funcionários.

---

## 👥 Perfis de usuário

| Perfil | Como é definido | O que acessa |
|---|---|---|
| **Visitante** | Não autenticado | Home, cardápio, detalhes, login e cadastro |
| **Aluno** | `PerfilUsuario.tipo = aluno` (padrão no cadastro) | Perfil, carrinho, pedidos e status |
| **Funcionário** | `PerfilUsuario.tipo = funcionario` ou usuário `is_staff` | Painel de pedidos, gerenciamento do cardápio e cadastro de funcionários |

> A conta da cantina **não faz pedidos**: ao tentar adicionar ao carrinho, o funcionário é redirecionado ao gerenciamento do cardápio.

Ao fazer login, o funcionário é levado ao painel da cantina e o aluno à página inicial.

---

## 🛠 Tecnologias

- **Python** 3.12+ (recomendado)
- **Django** ≥ 6.1
- **Pillow** ≥ 10.0 (upload de imagens dos produtos)
- **SQLite** (banco padrão de desenvolvimento)
- **HTML, CSS e JavaScript** puros nos templates (sem framework de front-end)

---

## 🗂 Estrutura do projeto

```
ChiquinhoLanches/
├── config/                  # Configurações do projeto (settings, urls, wsgi, asgi)
├── core/                    # Todos os models, permissões, validadores, signals e testes
│   ├── management/commands/popular_cardapio.py
│   ├── migrations/
│   ├── models.py
│   ├── permissions.py       # eh_funcionario e @funcionario_required
│   ├── validators.py        # validação de CPF
│   ├── signals.py           # cria Perfil e Carrinho ao criar usuário
│   ├── context_processors.py
│   └── tests.py
├── usuarios/                # Login, cadastro, perfil e cadastro de funcionários
├── produtos/                # Cardápio, detalhes e gerenciamento de produtos
├── pedidos/                 # Carrinho, pedidos, status e painel da cantina
│   └── services.py          # Regras: finalizar e cancelar pedido
├── templates/               # base.html, fragments (header/footer) e partials
├── static/                  # css/style.css, js/script.js, img/logo.png
├── media/                   # Imagens enviadas dos produtos
├── manage.py
├── requirements.txt
└── LICENSE
```

**Organização dos apps:** todos os *models* ficam no app `core`. Os apps `usuarios`, `produtos` e `pedidos` cuidam apenas das telas de cada área (views, urls, forms e templates). As regras mais sensíveis de pedido (finalizar e cancelar) ficam em `pedidos/services.py`.

---

## 🧩 Modelo de dados

```
User 1─1 PerfilUsuario
User 1─1 Carrinho 1─N ItemCarrinho N─1 Produto
User 1─N Pedido 1─N ItemPedido N─1 Produto
Pedido 1─N HistoricoStatus
Categoria 1─N Produto N─N Ingrediente
```

| Model | Descrição |
|---|---|
| `PerfilUsuario` | Tipo (aluno/funcionário), matrícula única, CPF único (guardado só com números), telefone |
| `Categoria` | Nome, descrição e ordem de exibição no cardápio |
| `Ingrediente` | Nome único; usado na busca e nos detalhes do produto |
| `Produto` | Categoria, nome, descrição, preço, estoque, ativo, imagem e ingredientes |
| `Carrinho` / `ItemCarrinho` | Carrinho persistente (um por usuário), com itens únicos por produto |
| `Pedido` | Status, total, observação (até 250 caracteres), dados de cancelamento e reembolso |
| `ItemPedido` | Quantidade e **preço unitário no momento da compra** |
| `HistoricoStatus` | Linha do tempo de cada mudança de status do pedido |

---

## 🌐 Rotas

Todas as rotas ficam na raiz do site.

| Área | Rota | Descrição | Acesso |
|---|---|---|---|
| Início | `/` | Página inicial | Público |
| Usuários | `/login/` | Login com matrícula e senha | Público |
| | `/cadastro/` | Cadastro de aluno | Público |
| | `/perfil/` | Perfil e resumo de pedidos | Logado |
| | `/sair/` | Encerrar sessão | Logado |
| | `/painel/funcionarios/novo/` | Cadastrar funcionário | Funcionário |
| Cardápio | `/cardapio/` | Lista com busca (`?q=`) e filtro (`?categoria=`) | Público |
| | `/produto/<id>/` | Detalhes do produto | Público |
| | `/painel/cardapio/` | Gerenciar produtos | Funcionário |
| | `/painel/cardapio/novo/` | Novo produto | Funcionário |
| | `/painel/cardapio/<id>/editar/` | Editar produto | Funcionário |
| | `/painel/cardapio/<id>/remover/` | Remover (ou desativar) produto | Funcionário |
| Carrinho | `/carrinho/` | Ver carrinho | Logado |
| | `/carrinho/adicionar/<produto_id>/` | Adicionar item | Logado |
| | `/carrinho/atualizar/<item_id>/` | Alterar quantidade | Logado |
| | `/carrinho/remover/<item_id>/` | Remover item | Logado |
| | `/carrinho/finalizar/` | Finalizar pedido | Logado |
| Pedidos | `/meus-pedidos/` | Pedidos em andamento e anteriores | Logado |
| | `/pedido/<id>/` | Status e histórico do pedido | Dono ou funcionário |
| | `/pedido/<id>/status.json` | Status em JSON | Dono ou funcionário |
| | `/pedido/<id>/cancelar/` | Cancelar pedido pendente | Dono |
| Painel | `/painel/` | Painel de pedidos | Funcionário |
| | `/painel/pedido/<id>/avancar/` | Avançar status | Funcionário |
| | `/painel/pedido/<id>/cancelar/` | Cancelar com justificativa | Funcionário |
| Admin | `/admin/` | Django Admin | Superusuário/staff |

---

## 📐 Regras de negócio

- **Permissões:** as funções administrativas só são acessíveis a funcionários autenticados. O aluno só vê e cancela os próprios pedidos (um pedido de outra pessoa retorna 404).
- **Estoque:** um produto só está disponível se estiver ativo e tiver estoque maior que zero. A quantidade no carrinho nunca ultrapassa o estoque, que é **validado novamente na finalização** (com `select_for_update` dentro de uma transação).
- **Integridade do pedido:** o preço de cada item é gravado no momento da compra, então alterações posteriores no cardápio não mudam pedidos antigos.
- **Fluxo de status:** `Pendente → Em preparação → Pronto → Entregue`. O cancelamento é um caminho alternativo.
- **Cancelamento pelo aluno:** só enquanto o pedido está pendente.
- **Cancelamento pela cantina:** exige justificativa (mínimo de 5 caracteres), é exibida ao aluno e marca o pedido como **reembolsado**.
- **Devolução ao estoque:** ao cancelar um pedido, as quantidades voltam ao estoque (inclusive quando o cancelamento é feito pelo admin).
- **Histórico preservado:** produto que já aparece em pedidos não é apagado; é **desativado** e sai do cardápio.
- **Cadastro:** matrícula de 3 a 20 caracteres (letras, números, ponto, traço ou sublinhado), CPF validado pelos dígitos verificadores, e-mail e matrícula únicos, senha de no mínimo 8 caracteres.

---

## 🚀 Como executar

### Pré-requisitos
- Python 3.12 ou superior
- Git

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/ChiquinhoLanches.git
cd ChiquinhoLanches

# 2. Crie e ative um ambiente virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie o banco de dados
python manage.py migrate

# 5. (Opcional) Popule o cardápio de exemplo
python manage.py popular_cardapio

# 6. Crie um superusuário para acessar o admin
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**.

### Criando o primeiro funcionário

O cadastro público cria apenas contas de **aluno**. Para o primeiro funcionário, use uma das opções:

1. Entre no **Django Admin** (`/admin/`), abra *Perfis de usuários* e altere o tipo do usuário para **Funcionário**; ou
2. Use o superusuário (`is_staff`), que já é tratado como funcionário.

Depois disso, o funcionário pode cadastrar os demais em `/painel/funcionarios/novo/`. O funcionário entra com a **matrícula** que foi cadastrada.

---

## 🌱 Dados de exemplo

O comando abaixo cria categorias, ingredientes e produtos para testar o sistema:

```bash
python manage.py popular_cardapio
```

Cria as categorias **Lanches**, **Salgados**, **Bebidas** e **Doces** (por exemplo: Hambúrguer, X-Salada, Coxinha, Pão de queijo, Suco de laranja e Brigadeiro). É seguro rodar mais de uma vez, pois não duplica nada.

---

## 🧪 Testes

O projeto possui uma suíte de testes automatizados em `core/tests.py`, cobrindo models, páginas públicas, usuários, área da cantina, carrinho, pedidos e painel.

```bash
python manage.py test
```

---

## 📋 Requisitos funcionais

Resumo dos requisitos documentados (detalhes no documento de requisitos):

| Grupo | Códigos | Resumo |
|---|---|---|
| Acesso e conta | RF01 a RF08 | Página inicial, cardápio, busca e filtro, detalhes, cadastro, login/logout, redirecionamento por perfil e perfil do usuário |
| Carrinho e pedidos | RF09 a RF16 | Adicionar ao carrinho, limite de estoque, consultar e alterar itens, finalizar com validação de estoque, registro de preços e observação |
| Acompanhamento e cancelamento | RF17 a RF23 | Lista de pedidos, status e histórico, cancelamento pelo aluno e pela cantina, justificativa, reembolso e devolução ao estoque |
| Operações da cantina | RF24 a RF31 | Painel de pedidos, resumo do dia, avanço de status, CRUD de produtos, cadastro de funcionários e restrição por permissão |

### Diagrama de casos de uso

Atores: **Visitante**, **Aluno** e **Funcionário da cantina**. Destaques do diagrama:

- *Consultar cardápio* é estendido por *Ver detalhes do produto* (`extend`).
- *Finalizar pedido* inclui *Validar estoque* (`include`).
- *Cancelar pedido (com justificativa)* inclui *Registrar justificativa e reembolso* (`include`).

---

## ⚠️ Observações para produção

As configurações atuais são voltadas ao **desenvolvimento**. Antes de publicar o sistema:

- Defina `DEBUG = False` e preencha `ALLOWED_HOSTS`.
- Troque a `SECRET_KEY` e leia-a de uma variável de ambiente (nunca a deixe no repositório).
- Configure um servidor de arquivos estáticos e de mídia (o `static()` do Django só serve `media/` com `DEBUG = True`).
- Considere um banco como PostgreSQL no lugar do SQLite.
- Configure um backend de e-mail real (atualmente o e-mail é exibido no console).

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

© 2026 Douglas & Caio 
