from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.EntrarView.as_view(), name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil, name='perfil'),
    path('painel/funcionarios/novo/', views.cadastro_funcionario, name='cadastro_funcionario'),
    path('sair/', LogoutView.as_view(), name='logout'),
]
