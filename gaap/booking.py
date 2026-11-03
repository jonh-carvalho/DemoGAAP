from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .availability import experimental_slot_is_available
from .models import (
    Agendamento,
    Aluno,
    Profissional,
    ReservaHorarioExperimental,
    Responsavel,
    Servico,
    SolicitacaoExperimental,
)


@transaction.atomic
def confirmar_solicitacao_experimental(solicitacao_id, usuario, data_nascimento):
    solicitacao = SolicitacaoExperimental.objects.select_for_update().get(pk=solicitacao_id)
    if solicitacao.status == SolicitacaoExperimental.STATUS_CONVERTIDA:
        raise ValidationError('Esta solicitação já foi convertida em agendamento.')

    reserva = (
        ReservaHorarioExperimental.objects.select_for_update()
        .filter(solicitacao=solicitacao)
        .first()
    )
    if reserva is None or reserva.expira_em <= timezone.now():
        raise ValidationError(
            'A reserva temporária expirou. Entre em contato com a família para escolher outro horário.'
        )

    profissional = Profissional.objects.select_for_update().get(pk=reserva.profissional_id)
    servico = Servico.objects.filter(tipo=Servico.TIPO_TREINO, ativo=True).order_by('id').first()
    if servico is None or not experimental_slot_is_available(
        servico,
        profissional,
        reserva.inicio,
        reserva.fim,
        exclude_hold_id=reserva.pk,
    ):
        raise ValidationError(
            'O horário não está mais disponível. Entre em contato com a família para combinar outra opção.'
        )
    reserva.delete()

    responsavel = Responsavel.objects.create(
        nome=solicitacao.nome_responsavel,
        telefone=solicitacao.telefone,
        email=solicitacao.email or None,
    )
    aluno = Aluno.objects.create(
        nome=solicitacao.nome_atleta,
        data_nascimento=data_nascimento,
        responsavel=responsavel,
    )
    agendamento = Agendamento(
        aluno=aluno,
        servico=servico,
        profissional=profissional,
        inicio=reserva.inicio,
        fim=reserva.fim,
        status=Agendamento.STATUS_CONFIRMADO,
        created_by=usuario,
        observacoes='Aula experimental confirmada pela administração do GAAP.',
    )
    agendamento.save()

    solicitacao.agendamento = agendamento
    solicitacao.status = SolicitacaoExperimental.STATUS_CONVERTIDA
    solicitacao.save(update_fields=['agendamento', 'status', 'updated_at'])
    return agendamento
