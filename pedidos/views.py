from django.shortcuts import render

# Create your views here.
def teste(request):
    return render(request, 'pedidos/pagina_teste2.html')