
function obterCarrinho() {
    try {
        return JSON.parse(
            localStorage.getItem("chiquinho_carrinho")
        ) || [];
    } catch {
        return [];
    }
}

function salvarCarrinho(carrinho) {
    localStorage.setItem(
        "chiquinho_carrinho",
        JSON.stringify(carrinho)
    );
}

function adicionarCarrinho(nome, preco) {
    const carrinho = obterCarrinho();

    preco = Number(String(preco).replace(",", "."));

    if (!Number.isFinite(preco) || preco < 0) {
        alert("Preço inválido para este produto.");
        return;
    }

    const produto = carrinho.find(item => item.nome === nome);

    if (produto) {
        produto.quantidade++;
    } else {
        carrinho.push({
            nome,
            preco,
            quantidade: 1
        });
    }

    salvarCarrinho(carrinho);
    alert(`${nome} adicionado ao carrinho!`);
}

function renderizarCarrinho() {
    const container = document.getElementById("itens-carrinho");
    const totalElement = document.getElementById("total-carrinho");

    if (!container || !totalElement) return;

    const carrinho = obterCarrinho();
    container.replaceChildren();

    if (carrinho.length === 0) {
        const mensagem = document.createElement("p");
        mensagem.className = "empty-state";
        mensagem.textContent = "Seu carrinho está vazio.";
        container.appendChild(mensagem);
        totalElement.textContent = "R$ 0,00";
        return;
    }

    let total = 0;

    carrinho.forEach((item, index) => {
        const subtotal = item.preco * item.quantidade;
        total += subtotal;

        const linha = document.createElement("div");
        linha.className = "cart-item";

        const descricao = document.createElement("span");
        descricao.textContent =
            `${item.nome} × ${item.quantidade} — ` +
            subtotal.toLocaleString("pt-BR", {
                style: "currency",
                currency: "BRL"
            });

        const remover = document.createElement("button");
        remover.className = "btn btn-secondary btn-small";
        remover.type = "button";
        remover.textContent = "Remover";

        remover.addEventListener("click", () => {
            const atualizado = obterCarrinho();
            atualizado.splice(index, 1);
            salvarCarrinho(atualizado);
            renderizarCarrinho();
        });

        linha.append(descricao, remover);
        container.appendChild(linha);
    });

    totalElement.textContent = total.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function finalizarPedido() {
    const carrinho = obterCarrinho();

    if (!carrinho.length) {
        alert("Seu carrinho está vazio!");
        return;
    }

    alert("A finalização de pedidos será integrada ao sistema em outra etapa.");
}

document.addEventListener("DOMContentLoaded", renderizarCarrinho);
