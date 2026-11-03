import re

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import PerfilUsuario
from core.validators import somente_digitos, validar_cpf

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Matrícula",
        widget=forms.TextInput(
            attrs={"autofocus": True, "autocomplete": "username", "inputmode": "text"}
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Matrícula ou senha incorretos.",
    }

    def clean(self):
        identificador = (self.cleaned_data.get("username") or "").strip()
        if identificador:
            perfil = (
                PerfilUsuario.objects.select_related("usuario")
                .filter(matricula__iexact=identificador)
                .first()
            )
            self.cleaned_data["username"] = (
                perfil.usuario.get_username() if perfil else identificador
            )
        return super().clean()


class CadastroForm(forms.Form):
    tipo = PerfilUsuario.Tipo.ALUNO
    rotulo_matricula = "Matrícula"

    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    matricula = forms.CharField(label="Matrícula", max_length=20)
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={"inputmode": "numeric", "placeholder": "000.000.000-00", "data-mascara": "cpf"}
        ),
    )
    telefone = forms.CharField(
        label="Telefone (opcional)",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"inputmode": "tel", "placeholder": "(00) 00000-0000", "data-mascara": "telefone"}
        ),
    )
    password1 = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Mínimo de 8 caracteres.",
    )
    password2 = forms.CharField(
        label="Confirmar senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matricula"].label = self.rotulo_matricula

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_matricula(self):
        matricula = self.cleaned_data["matricula"].strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,20}", matricula):
            raise ValidationError(
                "Use de 3 a 20 caracteres: letras, números, ponto, traço ou sublinhado."
            )
        if (
            PerfilUsuario.objects.filter(matricula__iexact=matricula).exists()
            or User.objects.filter(username__iexact=matricula).exists()
        ):
            raise ValidationError("Esta matrícula já está cadastrada.")
        return matricula

    def clean_cpf(self):
        cpf = self.cleaned_data["cpf"]
        validar_cpf(cpf)
        cpf = somente_digitos(cpf)
        if PerfilUsuario.objects.filter(cpf=cpf).exists():
            raise ValidationError("Este CPF já está cadastrado.")
        return cpf

    def clean(self):
        dados = super().clean()
        senha1, senha2 = dados.get("password1"), dados.get("password2")
        if senha1 and senha2:
            if senha1 != senha2:
                self.add_error("password2", "As senhas não são iguais.")
            else:
                provisorio = User(
                    username=dados.get("matricula", ""),
                    first_name=dados.get("first_name", ""),
                    last_name=dados.get("last_name", ""),
                    email=dados.get("email", ""),
                )
                try:
                    password_validation.validate_password(senha1, provisorio)
                except ValidationError as erro:
                    self.add_error("password1", erro)
        return dados

    @transaction.atomic
    def save(self):
        dados = self.cleaned_data
        user = User.objects.create_user(
            username=dados["matricula"],
            email=dados["email"],
            password=dados["password1"],
            first_name=dados["first_name"],
            last_name=dados["last_name"],
        )
        perfil = user.perfil  # criado por signal
        perfil.tipo = self.tipo
        perfil.matricula = dados["matricula"]
        perfil.cpf = dados["cpf"]
        perfil.telefone = dados["telefone"]
        perfil.save()
        return user


class CadastroFuncionarioForm(CadastroForm):
    """Mesmo formulário, usado pela própria cantina para cadastrar funcionários."""

    tipo = PerfilUsuario.Tipo.FUNCIONARIO
    rotulo_matricula = "Matrícula do funcionário"
