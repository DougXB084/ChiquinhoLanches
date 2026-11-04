from django import forms

from core.models import Categoria, Ingrediente, Produto


class ProdutoForm(forms.ModelForm):
    nova_categoria = forms.CharField(
        label="Ou crie uma categoria nova",
        max_length=100,
        required=False,
        help_text="Se preencher, ela é usada no lugar da categoria escolhida acima.",
    )
    novos_ingredientes = forms.CharField(
        label="Ingredientes novos",
        max_length=300,
        required=False,
        help_text="Separe por vírgula. Ex.: Bacon, Molho especial",
    )

    class Meta:
        model = Produto
        fields = [
            "nome",
            "descricao",
            "categoria",
            "preco",
            "estoque",
            "ativo",
            "imagem",
            "ingredientes",
        ]
        labels = {
            "descricao": "Descrição",
            "preco": "Preço (R$)",
            "ativo": "Disponível no cardápio",
            "imagem": "Foto",
        }
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "ingredientes": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = False
        self.fields["categoria"].empty_label = "Escolha uma categoria"
        self.fields["ingredientes"].required = False
        self.fields["preco"].min_value = 0
        self.fields["preco"].widget.attrs.update({"min": "0", "step": "0.01"})

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco <= 0:
            raise forms.ValidationError("O preço precisa ser maior que zero.")
        return preco

    def clean(self):
        dados = super().clean()
        if not dados.get("categoria") and not (dados.get("nova_categoria") or "").strip():
            self.add_error("categoria", "Escolha uma categoria ou crie uma nova.")
        return dados

    def save(self, commit=True):
        nova = (self.cleaned_data.get("nova_categoria") or "").strip()
        if nova:
            self.instance.categoria = (
                Categoria.objects.filter(nome__iexact=nova).first()
                or Categoria.objects.create(nome=nova)
            )
        produto = super().save(commit=commit)
        if commit:
            for nome in self.cleaned_data.get("novos_ingredientes", "").split(","):
                nome = nome.strip()
                if not nome:
                    continue
                ingrediente = (
                    Ingrediente.objects.filter(nome__iexact=nome).first()
                    or Ingrediente.objects.create(nome=nome[:80])
                )
                produto.ingredientes.add(ingrediente)
        return produto
