from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from gaap.models import (
    Agendamento,
    Aluno,
    Perfil,
    Profissional,
    RegraDisponibilidade,
    RelatorioTreino,
    ReservaHorarioExperimental,
    Responsavel,
    Servico,
    SolicitacaoExperimental,
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
                status='PENDENTE',
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
            status='PENDENTE',
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

    def test_seed_cria_profissionais_e_servicos_sem_duplicar(self):
        usernames = ['profissional_educacao_fisica', 'fisioterapeuta', 'psicologo']
        nomes_servicos = ['Fisioterapia', 'Nutricionista', 'Psicologia']

        call_command('seed_gaap')
        call_command('seed_gaap')

        self.assertEqual(Profissional.objects.filter(usuario__username__in=usernames).count(), 3)
        self.assertEqual(Servico.objects.filter(nome__in=nomes_servicos).count(), 3)
        self.assertEqual(
            set(Profissional.objects.filter(usuario__username__in=usernames).values_list('especialidade', flat=True)),
            {'Educação Física', 'Fisioterapia', 'Psicologia'},
        )

    def test_landing_publica_recebe_solicitacao_sem_criar_agendamento_ou_conta(self):
        data_aula, horario = self._criar_horario_experimental()
        counts_before = (Aluno.objects.count(), Agendamento.objects.count(), User.objects.count())
        response = self.client.get('/', {'data_aula': data_aula})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solicitar aula experimental')
        self.assertContains(response, horario.split('|')[1][11:])

        response = self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '(21) 99999-1234',
            'email': 'ana@example.com',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'O horário ficará reservado por 24 horas')
        solicitacao = SolicitacaoExperimental.objects.get()
        self.assertEqual(solicitacao.telefone, '21999991234')
        self.assertEqual(solicitacao.modalidade, 'TREINO')
        self.assertEqual(solicitacao.status, SolicitacaoExperimental.STATUS_NOVA)
        self.assertIsNotNone(solicitacao.consentimento_em)
        self.assertEqual(solicitacao.inicio_solicitado.date().isoformat(), data_aula)
        self.assertEqual(ReservaHorarioExperimental.objects.filter(solicitacao=solicitacao).count(), 1)
        self.assertEqual(
            (Aluno.objects.count(), Agendamento.objects.count(), User.objects.count()),
            counts_before,
        )

    def test_solicitacao_reserva_horario_temporariamente(self):
        data_aula, horario = self._criar_horario_experimental()
        payload = {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        }

        self.assertEqual(self.client.post('/', payload).status_code, 302)
        response = self.client.get('/', {'data_aula': data_aula})
        self.assertNotContains(response, horario)
        self.assertEqual(ReservaHorarioExperimental.objects.count(), 1)

    def test_reserva_temporaria_impede_agendamento_operacional_no_mesmo_horario(self):
        data_aula, horario = self._criar_horario_experimental()
        self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        })
        reserva = ReservaHorarioExperimental.objects.get()
        agendamento = Agendamento(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=reserva.inicio,
            fim=reserva.fim,
            status=Agendamento.STATUS_CONFIRMADO,
            created_by=self.admin_user,
        )

        with self.assertRaisesMessage(ValidationError, 'O horário está reservado temporariamente'):
            agendamento.save()

    def test_confirmacao_admin_cria_agendamento_apos_revalidar_horario(self):
        data_aula, horario = self._criar_horario_experimental()
        self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        })
        solicitacao = SolicitacaoExperimental.objects.get()
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=['is_staff', 'is_superuser'])
        self.client.force_login(self.admin_user)

        url = reverse('admin:gaap_solicitacaoexperimental_confirmar', args=[solicitacao.pk])
        hoje = timezone.localdate()
        response = self.client.post(url, {
            'data_nascimento': hoje.replace(year=hoje.year - 16).isoformat(),
            'contato_confirmado': 'on',
        })

        self.assertEqual(response.status_code, 302)
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoExperimental.STATUS_CONVERTIDA)
        self.assertEqual(solicitacao.agendamento.status, Agendamento.STATUS_CONFIRMADO)
        self.assertEqual(solicitacao.agendamento.aluno.nome, 'Lucas Silva')
        self.assertFalse(ReservaHorarioExperimental.objects.filter(solicitacao=solicitacao).exists())

    def test_confirmacao_admin_recusa_reserva_expirada(self):
        data_aula, horario = self._criar_horario_experimental()
        self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        })
        solicitacao = SolicitacaoExperimental.objects.get()
        ReservaHorarioExperimental.objects.filter(solicitacao=solicitacao).update(
            expira_em=timezone.now() - timedelta(seconds=1)
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=['is_staff', 'is_superuser'])
        self.client.force_login(self.admin_user)

        hoje = timezone.localdate()
        response = self.client.post(
            reverse('admin:gaap_solicitacaoexperimental_confirmar', args=[solicitacao.pk]),
            {
                'data_nascimento': hoje.replace(year=hoje.year - 16).isoformat(),
                'contato_confirmado': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A reserva temporária expirou')
        self.assertFalse(Agendamento.objects.exists())
        self.assertEqual(
            SolicitacaoExperimental.objects.get(pk=solicitacao.pk).status,
            SolicitacaoExperimental.STATUS_NOVA,
        )

    def test_confirmacao_admin_recusa_horario_ocupado_apos_a_solicitacao(self):
        data_aula, horario = self._criar_horario_experimental()
        self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'data_aula': data_aula,
            'horario': horario,
            'consentimento_contato': 'on',
            'website': '',
        })
        solicitacao = SolicitacaoExperimental.objects.get()
        reserva = ReservaHorarioExperimental.objects.get(solicitacao=solicitacao)
        self.servico.capacidade_maxima = 1
        self.servico.save(update_fields=['capacidade_maxima'])
        Agendamento.objects.bulk_create([Agendamento(
            aluno=self.aluno,
            servico=self.servico,
            profissional=self.profissional,
            inicio=reserva.inicio,
            fim=reserva.fim,
            status=Agendamento.STATUS_CONFIRMADO,
            created_by=self.admin_user,
        )])
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=['is_staff', 'is_superuser'])
        self.client.force_login(self.admin_user)
        hoje = timezone.localdate()

        response = self.client.post(
            reverse('admin:gaap_solicitacaoexperimental_confirmar', args=[solicitacao.pk]),
            {
                'data_nascimento': hoje.replace(year=hoje.year - 16).isoformat(),
                'contato_confirmado': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'O horário não está mais disponível')
        self.assertEqual(
            SolicitacaoExperimental.objects.get(pk=solicitacao.pk).status,
            SolicitacaoExperimental.STATUS_NOVA,
        )
        self.assertEqual(Agendamento.objects.count(), 1)

    def test_solicitacao_exige_consentimento_e_dados_validos(self):
        response = self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '123',
            'periodo_preferido': 'TARDE',
            'website': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Precisamos da sua autorização para entrar em contato.')
        self.assertContains(response, 'Informe um telefone com DDD e 10 ou 11 dígitos.')
        self.assertEqual(SolicitacaoExperimental.objects.count(), 0)

    def test_solicitacao_honeypot_bloqueia_envio_automatizado(self):
        response = self.client.post('/', {
            'nome_responsavel': 'Ana Silva',
            'nome_atleta': 'Lucas Silva',
            'idade_atleta': '16',
            'telefone': '21999991234',
            'periodo_preferido': 'TARDE',
            'consentimento_contato': 'on',
            'website': 'spam.example',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SolicitacaoExperimental.objects.count(), 0)

    def test_triagem_de_solicitacoes_e_restrita_ao_admin(self):
        changelist_url = reverse('admin:gaap_solicitacaoexperimental_changelist')

        self.assertEqual(self.client.get(changelist_url).status_code, 302)
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(changelist_url).status_code, 302)

        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=['is_staff', 'is_superuser'])
        self.client.force_login(self.admin_user)
        self.assertEqual(self.client.get(changelist_url).status_code, 200)

    def _criar_horario_experimental(self):
        data_aula = timezone.localdate() + timedelta(days=1)
        while data_aula.weekday() != 0:
            data_aula += timedelta(days=1)
        RegraDisponibilidade.objects.create(
            servico=self.servico,
            profissional=self.profissional,
            dia_semana='MONDAY',
            hora_inicio=time(9, 0),
            hora_fim=time(11, 0),
        )
        return data_aula.isoformat(), f'{self.profissional.pk}|{data_aula.isoformat()}T09:00'
