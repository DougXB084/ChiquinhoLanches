from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from core.models import Pedido, PerfilUsuario
from core.permissions import eh_funcionario, funcionario_required

from .forms import CadastroForm, CadastroFuncionarioForm, LoginForm


class EntrarView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        destino = self.get_redirect_url()
        if destino:
            return destino
        if eh_funcionario(self.request.user):
            return reverse("pedidos:painel")
        return reverse("core:home")

    def form_valid(self, form):
        usuario = form.get_user()
        messages.success(
            self.request, f"Bem-vindo de volta, {usuario.first_name or usuario.username}!"
        )
        return super().form_valid(form)


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    proximo = request.POST.get("next") or request.GET.get("next", "")
    form = CadastroForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Conta criada! Já pode escolher seu lanche.")
        if proximo and url_has_allowed_host_and_scheme(
            proximo, allowed_hosts={request.get_host()}
        ):
            return redirect(proximo)
        return redirect("produtos:cardapio")

    return render(
        request, "usuarios/cadastro.html", {"form": form, "next": proximo, "funcionario": False}
    )


@funcionario_required
def cadastro_funcionario(request):
    form = CadastroFuncionarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        novo = form.save()
        messages.success(
            request,
            f"{novo.get_full_name()} foi cadastrado como funcionário. "
            f"Ele entra com a matrícula {novo.perfil.matricula}.",
        )
        return redirect("pedidos:painel")
    return render(
        request, "usuarios/cadastro.html", {"form": form, "funcionario": True}
    )


@login_required
def perfil(request):
    perfil_usuario, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    pedidos = Pedido.objects.filter(usuario=request.user)
    contexto = {
        "perfil": perfil_usuario,
        "total_pedidos": pedidos.count(),
        "pedidos_entregues": pedidos.filter(status=Pedido.Status.ENTREGUE).count(),
        "pedidos_em_andamento": sum(1 for p in pedidos if p.em_andamento),
    }
    return render(request, "usuarios/perfil.html", contexto)
