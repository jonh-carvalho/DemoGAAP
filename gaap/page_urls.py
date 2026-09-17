from django.urls import path

from . import page_views

urlpatterns = [
    path('', page_views.home, name='home'),
    path('login/', page_views.login_page, name='login_page'),
    path('dashboard/', page_views.dashboard, name='dashboard'),
    path('servicos/', page_views.servicos, name='servicos_page'),
    path('agendamentos/', page_views.agendamentos, name='agendamentos_page'),
    path('presencas/', page_views.presencas, name='presencas_page'),
]
