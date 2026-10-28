from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'core/pagina_teste1.html')