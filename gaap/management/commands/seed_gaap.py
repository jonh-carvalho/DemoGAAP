from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from gaap.models import (
    Agendamento,
    Aluno,
    Perfil,
    Profissional,
    Responsavel,
    Servico,
    Usuario,
)


class Command(BaseCommand):
    help = 'Cria dados iniciais para o MVP do GAAP'

    def handle(self, *args, **options):
        admin_perfil, _ = Perfil.objects.get_or_create(codigo='ADMIN', defaults={'nome': 'Administrador'})
        treinador_perfil, _ = Perfil.objects.get_or_create(codigo='TREINADOR', defaults={'nome': 'Treinador'})
        saude_perfil, _ = Perfil.objects.get_or_create(codigo='SAUDE', defaults={'nome': 'Profissional de Saúde'})

        admin_user, _ = Usuario.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@gaap.com', 'perfil': admin_perfil, 'is_staff': True, 'is_superuser': True},
        )
        admin_user.perfil = admin_perfil
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password('Senha123')
        admin_user.save()

        treinador_user, _ = Usuario.objects.get_or_create(
            username='treinador',
            defaults={'email': 'treinador@gaap.com', 'perfil': treinador_perfil},
        )
        treinador_user.perfil = treinador_perfil
        treinador_user.is_active = True
        treinador_user.set_password('Senha123')
        treinador_user.save()

        profissional_user, _ = Usuario.objects.get_or_create(
            username='profissional',
            defaults={'email': 'profissional@gaap.com', 'perfil': saude_perfil},
        )
        profissional_user.perfil = saude_perfil
        profissional_user.is_active = True
        profissional_user.set_password('Senha123')
        profissional_user.save()

        profissionais_adicionais = [
            {
                'username': 'profissional_educacao_fisica',
                'email': 'educacao.fisica@gaap.com',
                'perfil': treinador_perfil,
                'nome': 'Profissional de Educação Física',
                'especialidade': 'Educação Física',
            },
            {
                'username': 'fisioterapeuta',
                'email': 'fisioterapia@gaap.com',
                'perfil': saude_perfil,
                'nome': 'Fisioterapeuta GAAP',
                'especialidade': 'Fisioterapia',
            },
            {
                'username': 'psicologo',
                'email': 'psicologia@gaap.com',
                'perfil': saude_perfil,
                'nome': 'Psicólogo GAAP',
                'especialidade': 'Psicologia',
            },
        ]
        for dados in profissionais_adicionais:
            usuario, criado = Usuario.objects.get_or_create(
                username=dados['username'],
                defaults={
                    'email': dados['email'],
                    'perfil': dados['perfil'],
                    'is_active': True,
                },
            )
            if criado or not usuario.has_usable_password():
                usuario.set_password('Senha123')
            usuario.email = dados['email']
            usuario.perfil = dados['perfil']
            usuario.is_active = True
            usuario.save()
            Profissional.objects.update_or_create(
                usuario=usuario,
                defaults={
                    'nome': dados['nome'],
                    'especialidade': dados['especialidade'],
                    'ativo': True,
                },
            )

        responsavel, _ = Responsavel.objects.get_or_create(
            nome='Maria da Silva',
            defaults={'telefone': '11999990000', 'email': 'maria@email.com'},
        )

        aluno, _ = Aluno.objects.get_or_create(
            nome='João da Silva',
            defaults={'data_nascimento': '2012-01-15', 'responsavel': responsavel},
        )

        servico_treino, _ = Servico.objects.get_or_create(
            nome='Treino',
            defaults={'tipo': 'TREINO', 'duracao_minutos': 60, 'capacidade_maxima': 6, 'ativo': True},
        )

        for nome, tipo in [
            ('Fisioterapia', 'FISIOTERAPIA'),
            ('Nutricionista', 'NUTRICAO'),
            ('Psicologia', 'PSICOLOGIA'),
        ]:
            Servico.objects.get_or_create(
                nome=nome,
                defaults={
                    'tipo': tipo,
                    'duracao_minutos': 30,
                    'capacidade_maxima': 1,
                    'ativo': True,
                },
            )

        profissional, _ = Profissional.objects.get_or_create(
            usuario=profissional_user,
            defaults={'nome': 'Carla Nutricionista', 'especialidade': 'Nutrição', 'ativo': True},
        )

        base_inicio = timezone.make_aware(datetime(2026, 9, 18, 9, 0), timezone.get_current_timezone())
        base_fim = base_inicio + timedelta(minutes=60)

        Agendamento.objects.get_or_create(
            aluno=aluno,
            servico=servico_treino,
            profissional=profissional,
            inicio=base_inicio,
            fim=base_fim,
            defaults={'status': 'CONFIRMADO', 'created_by': admin_user},
        )

        self.stdout.write(self.style.SUCCESS('Dados iniciais do GAAP criados com sucesso.'))
