from django.shortcuts import render

# Create your views here.
def teste(request):
    return render(request, 'usuarios/pagina_teste4.html')