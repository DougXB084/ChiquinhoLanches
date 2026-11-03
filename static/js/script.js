/* Chiquinho Lanches — comportamentos leves das páginas */

document.addEventListener("DOMContentLoaded", () => {

    /* Menu do celular */
    const navbar = document.querySelector(".navbar");
    const toggle = document.querySelector(".navbar-toggle");
    if (navbar && toggle) {
        toggle.addEventListener("click", () => {
            const aberto = navbar.classList.toggle("aberto");
            toggle.setAttribute("aria-expanded", String(aberto));
            toggle.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
        });
    }

    /* Mensagens do Django somem sozinhas */
    document.querySelectorAll(".messages li").forEach((item) => {
        setTimeout(() => {
            item.classList.add("saindo");
            setTimeout(() => item.remove(), 400);
        }, 6000);
    });

    /* Seletor de quantidade (+ / −) */
    document.querySelectorAll(".stepper").forEach((stepper) => {
        const campo = stepper.querySelector("input[type='number']");
        const form = stepper.closest("form");

        const enviarSeNecessario = () => {
            if (form && form.hasAttribute("data-autosubmit")) {
                form.requestSubmit();
            }
        };

        stepper.querySelectorAll("[data-step]").forEach((botao) => {
            botao.addEventListener("click", () => {
                const passo = Number(botao.dataset.step);
                const minimo = Number(campo.min || 1);
                const maximo = campo.max ? Number(campo.max) : Infinity;
                const atual = Number(campo.value) || minimo;
                const novo = Math.min(Math.max(atual + passo, minimo), maximo);
                if (novo === atual) return;
                campo.value = novo;
                enviarSeNecessario();
            });
        });

        campo.addEventListener("change", enviarSeNecessario);
    });

    /* Busca instantânea no cardápio (o envio do formulário continua funcionando) */
    const busca = document.querySelector("[data-filtro-cardapio]");
    const cartoes = document.querySelectorAll("#lista-produtos .produto-card");
    const semResultados = document.getElementById("sem-resultados");
    if (busca && cartoes.length) {
        const filtrar = () => {
            const termo = busca.value.trim().toLowerCase();
            let visiveis = 0;
            cartoes.forEach((cartao) => {
                const mostrar = !termo || cartao.dataset.nome.includes(termo);
                cartao.hidden = !mostrar;
                if (mostrar) visiveis += 1;
            });
            if (semResultados) semResultados.hidden = visiveis > 0;
        };
        busca.addEventListener("input", filtrar);
        filtrar();
    }

    /* Máscaras de CPF e telefone */
    const somenteDigitos = (v) => v.replace(/\D/g, "");
    const mascaras = {
        cpf: (v) => {
            const d = somenteDigitos(v).slice(0, 11);
            return d
                .replace(/^(\d{3})(\d)/, "$1.$2")
                .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
                .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
        },
        telefone: (v) => {
            const d = somenteDigitos(v).slice(0, 11);
            if (d.length <= 2) return d;
            if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
            if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
            return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
        },
    };
    document.querySelectorAll("[data-mascara]").forEach((campo) => {
        const aplicar = mascaras[campo.dataset.mascara];
        if (!aplicar) return;
        campo.addEventListener("input", () => { campo.value = aplicar(campo.value); });
        if (campo.value) campo.value = aplicar(campo.value);
    });

    /* Confirmação antes de ações irreversíveis */
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (evento) => {
            if (!window.confirm(form.dataset.confirm)) {
                evento.preventDefault();
            }
        });
    });

    /* Tela de status: recarrega quando a cantina muda o status do pedido */
    const acompanhamento = document.querySelector("[data-status-url]");
    if (acompanhamento) {
        const url = acompanhamento.dataset.statusUrl;
        const statusAtual = acompanhamento.dataset.statusAtual;
        setInterval(async () => {
            if (document.hidden) return;
            try {
                const resposta = await fetch(url, { headers: { Accept: "application/json" } });
                if (!resposta.ok) return;
                const dados = await resposta.json();
                if (dados.status !== statusAtual) window.location.reload();
            } catch (erro) {
                /* sem conexão: tenta de novo no próximo ciclo */
            }
        }, 15000);
    }

    /* Painel da cantina: atualiza a fila sozinho */
    const painel = document.querySelector("[data-auto-reload]");
    if (painel) {
        const segundos = Number(painel.dataset.autoReload) || 30;
        setInterval(() => {
            if (document.hidden) return;
            // Não recarrega enquanto alguém está escrevendo uma justificativa.
            const digitando = document.querySelector(".cancelar-pedido[open]");
            const comTexto = [...document.querySelectorAll(".cancelar-pedido textarea")].some((t) => t.value.trim());
            if (digitando || comTexto) return;
            window.location.reload();
        }, segundos * 1000);
    }
});
