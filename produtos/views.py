from django.shortcuts import render

# Create your views here.
def teste(request):
    return render(request, 'produtos/pagina_teste3.html')