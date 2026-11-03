import re

from django.core.exceptions import ValidationError


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def validar_cpf(valor):
    cpf = somente_digitos(valor)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("Informe um CPF válido.")
    for posicao in (9, 10):
        soma = sum(int(cpf[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[posicao]):
            raise ValidationError("Informe um CPF válido.")
