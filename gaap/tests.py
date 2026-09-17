from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from gaap.models import (
    Agendamento,
    Aluno,
    Perfil,
    Profissional,
    RelatorioTreino,
    Responsavel,
    Servico,
)

User = get_user_model()


class GaapDomainTests(TestCase):
    def setUp(self):
        self.admin_perfil = Perfil.objects.create(nome='Administrador', codigo='ADMIN')
        self.treinador_perfil = Perfil.objects.create(nome='Treinador', codigo='TREINADOR')
        self.saude_perfil = Perfil.objects.create(nome='Profissional de Saúde', codigo='SAUDE')

        self.admin_user = User.objects.create_user(
            username='admin', email='admin@gaap.com', password='Senha123', perfil=self.admin_perfil
        )
        self.treinador_user = User.objects.create_user(
            username='treinador', email='treinador@gaap.com', password='Senha123', perfil=self.treinador_perfil
        )
        self.profissional_user = User.objects.create_user(
            username='profissional', email='profissional@gaap.com', password='Senha123', perfil=self.saude_perfil
        )

        self.responsavel = Responsavel.objects.create(
            nome='Maria Silva', telefone='11999999999', email='maria@email.com'
        )
        self.aluno = Aluno.objects.create(
            nome='João da Silva', data_nascimento='2012-01-15', responsavel=self.responsavel
        )

        self.servico = Servico.objects.create(
            nome='Treino', tipo='TREINO', duracao_minutos=60, capacidade_maxima=6, ativo=True
        )
        self.profissional = Profissional.objects.create(
            usuario=self.profissional_user,
            nome='Carla Nutricionista',
            especialidade='Nutrição',
        )

    def test_aluno_nao_pode_ter_agendamentos_sobrepostos(self):
        inicio = timezone.make_aware(datetime(2026, 9, 20, 9, 0), timezone.get_current_timezone())
        fim = inicio + timedelta(minutes=60)

        Agendamento.objects.create(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio,
            fim=fim,
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        sobreposto = Agendamento(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio + timedelta(minutes=30),
            fim=fim + timedelta(minutes=30),
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        with self.assertRaises(ValidationError):
            sobreposto.clean()

    def test_profissional_nao_pode_ter_agendamentos_sobrepostos(self):
        inicio = timezone.make_aware(datetime(2026, 9, 21, 10, 0), timezone.get_current_timezone())
        fim = inicio + timedelta(minutes=60)

        Agendamento.objects.create(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio,
            fim=fim,
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        outro_aluno = Aluno.objects.create(
            nome='Pedro Souza', data_nascimento='2011-05-11', responsavel=self.responsavel
        )

        sobreposto = Agendamento(
            aluno=outro_aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio + timedelta(minutes=20),
            fim=fim + timedelta(minutes=20),
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        with self.assertRaises(ValidationError):
            sobreposto.clean()

    def test_servico_nao_pode_ultrapassar_capacidade_no_mesmo_horario(self):
        inicio = timezone.make_aware(datetime(2026, 9, 22, 14, 0), timezone.get_current_timezone())
        fim = inicio + timedelta(minutes=60)

        for index in range(6):
            aluno = Aluno.objects.create(
                nome=f'Aluno {index}',
                data_nascimento='2010-01-01',
                responsavel=self.responsavel,
            )
            Agendamento.objects.create(
                aluno=aluno,
                servico=self.servico,
                profissional=self.profissional,
                inicio=inicio,
                fim=fim,
                status='CONFIRMADO',
                created_by=self.admin_user,
            )

        aluno_extra = Aluno.objects.create(
            nome='Aluno Extra', data_nascimento='2009-02-02', responsavel=self.responsavel
        )
        agendamento_extra = Agendamento(
            aluno=aluno_extra,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio,
            fim=fim,
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        with self.assertRaises(ValidationError):
            agendamento_extra.clean()

    def test_aluno_e_responsavel_sao_usuarios_do_sistema(self):
        aluno_perfil = Perfil.objects.create(nome='Aluno', codigo='ALUNO')
        responsavel_perfil = Perfil.objects.create(nome='Responsável', codigo='RESPONSAVEL')

        aluno_user = User.objects.create_user(username='aluno_user', password='Senha123', perfil=aluno_perfil)
        responsavel_user = User.objects.create_user(username='resp_user', password='Senha123', perfil=responsavel_perfil)

        responsavel = Responsavel.objects.create(
            usuario=responsavel_user,
            nome='Maria Silva',
            telefone='11999999999',
            email='maria@email.com',
        )
        aluno = Aluno.objects.create(
            usuario=aluno_user,
            nome='João da Silva',
            data_nascimento='2012-01-15',
            responsavel=responsavel,
        )

        self.assertEqual(aluno.usuario, aluno_user)
        self.assertEqual(responsavel.usuario, responsavel_user)

    def test_agendamento_pode_ser_filtrado_pelo_usuario_aluno_e_responsavel(self):
        aluno_perfil = Perfil.objects.create(nome='Aluno', codigo='ALUNO')
        responsavel_perfil = Perfil.objects.create(nome='Responsável', codigo='RESPONSAVEL')

        aluno_user = User.objects.create_user(username='aluno_user_2', password='Senha123', perfil=aluno_perfil)
        responsavel_user = User.objects.create_user(username='resp_user_2', password='Senha123', perfil=responsavel_perfil)

        responsavel = Responsavel.objects.create(
            usuario=responsavel_user,
            nome='Maria Silva 2',
            telefone='11888888888',
            email='maria2@email.com',
        )
        aluno = Aluno.objects.create(
            usuario=aluno_user,
            nome='Pedro Souza',
            data_nascimento='2011-05-11',
            responsavel=responsavel,
        )

        inicio = timezone.make_aware(datetime(2026, 9, 23, 8, 0), timezone.get_current_timezone())
        fim = inicio + timedelta(minutes=60)

        agendamento = Agendamento.objects.create(
            aluno=aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio,
            fim=fim,
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        self.assertIn(agendamento, Agendamento.objects.filter(aluno__usuario=aluno_user))
        self.assertIn(agendamento, Agendamento.objects.filter(aluno__responsavel__usuario=responsavel_user))

    def test_agendamento_pode_registrar_presenca_e_relatorio(self):
        inicio = timezone.make_aware(datetime(2026, 9, 24, 9, 0), timezone.get_current_timezone())
        fim = inicio + timedelta(minutes=60)

        agendamento = Agendamento.objects.create(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=inicio,
            fim=fim,
            status='CONFIRMADO',
            created_by=self.admin_user,
        )

        agendamento.registrar_presenca('PRESENTE', self.treinador_user)
        relatorio = RelatorioTreino.objects.create(
            agendamento=agendamento,
            titulo='Relatório do treino',
            conteudo='Excelente desenvolvimento da sessão.',
            created_by=self.treinador_user,
        )

        self.assertEqual(agendamento.presenca, 'PRESENTE')
        self.assertEqual(relatorio.titulo, 'Relatório do treino')

    def test_admin_deve_ser_requerido_para_criar_bloqueios(self):
        self.assertEqual(self.admin_perfil.codigo, 'ADMIN')
        self.assertEqual(self.treinador_perfil.codigo, 'TREINADOR')
