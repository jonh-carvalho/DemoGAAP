from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AgendamentoViewSet,
    AlunoViewSet,
    BloqueioAgendaViewSet,
    ProfissionalViewSet,
    RelatorioTreinoViewSet,
    ResponsavelViewSet,
    ServicoViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'responsaveis', ResponsavelViewSet)
router.register(r'alunos', AlunoViewSet)
router.register(r'servicos', ServicoViewSet)
router.register(r'profissionais', ProfissionalViewSet)
router.register(r'agendamentos', AgendamentoViewSet)
router.register(r'bloqueios', BloqueioAgendaViewSet)
router.register(r'relatorios', RelatorioTreinoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
