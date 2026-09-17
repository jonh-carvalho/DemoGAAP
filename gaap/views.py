from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Agendamento, Aluno, BloqueioAgenda, Perfil, Profissional, RelatorioTreino, Responsavel, Servico, Usuario
from .permissions import IsAdmin, IsAdminOrTreinador, IsAlunoOrResponsavel, IsProfissionalSaude, IsTreinador
from .serializers import (
    AgendamentoSerializer,
    AlunoSerializer,
    BloqueioAgendaSerializer,
    PerfilSerializer,
    ProfissionalSerializer,
    RelatorioTreinoSerializer,
    ResponsavelSerializer,
    ServicoSerializer,
    UsuarioSerializer,
)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('perfil').all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdmin]


class PerfilViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [IsAdmin]


class ResponsavelViewSet(viewsets.ModelViewSet):
    queryset = Responsavel.objects.select_related('usuario', 'usuario__perfil').all()
    serializer_class = ResponsavelSerializer
    permission_classes = [IsAdminOrTreinador]

    def get_queryset(self):
        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.codigo == 'RESPONSAVEL':
            return self.queryset.filter(usuario=user)
        return self.queryset


class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.select_related('usuario', 'responsavel').all()
    serializer_class = AlunoSerializer
    permission_classes = [IsAdminOrTreinador]

    def get_queryset(self):
        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.codigo in {'ALUNO', 'RESPONSAVEL'}:
            return self.queryset.filter(usuario_id=user.id) | self.queryset.filter(responsavel__usuario_id=user.id)
        return super().get_queryset()

    @action(detail=False, methods=['get'], url_path='buscar')
    def buscar(self, request):
        termo = request.query_params.get('q', '').strip()
        if not termo:
            return Response({'detail': 'Informe um termo para busca.'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().filter(nome__icontains=termo)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ServicoViewSet(viewsets.ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [IsAdmin]


class ProfissionalViewSet(viewsets.ModelViewSet):
    queryset = Profissional.objects.select_related('usuario', 'usuario__perfil').all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAdminOrTreinador]


class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.select_related('aluno', 'servico', 'profissional', 'created_by').all()
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAdminOrTreinador | IsAlunoOrResponsavel]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.codigo == 'TREINADOR':
            return queryset.filter(profissional__usuario=user)
        if perfil and perfil.codigo == 'SAUDE':
            return queryset.filter(profissional__usuario=user)
        if perfil and perfil.codigo == 'ALUNO':
            return queryset.filter(aluno__usuario=user)
        if perfil and perfil.codigo == 'RESPONSAVEL':
            return queryset.filter(aluno__responsavel__usuario=user)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        if perfil and perfil.codigo in {'ALUNO', 'RESPONSAVEL'}:
            serializer.save(created_by=user)
            return
        serializer.save(created_by=user)


class BloqueioAgendaViewSet(viewsets.ModelViewSet):
    queryset = BloqueioAgenda.objects.select_related('servico', 'profissional', 'created_by').all()
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RelatorioTreinoViewSet(viewsets.ModelViewSet):
    queryset = RelatorioTreino.objects.select_related('agendamento', 'created_by').all()
    serializer_class = RelatorioTreinoSerializer
    permission_classes = [IsAdminOrTreinador]

    @action(detail=True, methods=['post'], url_path='marcar-presenca')
    def marcar_presenca(self, request, pk=None):
        agendamento = self.get_object().agendamento
        valor = request.data.get('presenca')
        try:
            agendamento.registrar_presenca(valor, request.user)
            return Response({'status': 'ok', 'presenca': agendamento.presenca})
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
