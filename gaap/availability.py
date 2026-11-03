from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import (
    Agendamento,
    BloqueioAgenda,
    ReservaHorarioExperimental,
    RegraDisponibilidade,
    Servico,
)


DAY_CODES = tuple(code for code, _ in RegraDisponibilidade.DIAS_SEMANA_CHOICES)


def expire_temporary_holds():
    ReservaHorarioExperimental.objects.filter(expira_em__lte=timezone.now()).delete()


def available_experimental_slots(data):
    if data < timezone.localdate():
        return []

    expire_temporary_holds()
    servico = Servico.objects.filter(tipo=Servico.TIPO_TREINO, ativo=True).order_by('id').first()
    if servico is None or servico.duracao_minutos <= 0:
        return []

    day_code = DAY_CODES[data.weekday()]
    rules = RegraDisponibilidade.objects.filter(
        servico=servico,
        profissional__ativo=True,
        dia_semana__iexact=day_code,
    ).select_related('profissional')
    slots = []
    seen = set()
    duration = timedelta(minutes=servico.duracao_minutos)

    for rule in rules:
        start_time = rule.hora_inicio
        while datetime.combine(data, start_time) + duration <= datetime.combine(data, rule.hora_fim):
            start = timezone.make_aware(
                datetime.combine(data, start_time),
                timezone.get_current_timezone(),
            )
            end = start + duration
            start_time = (datetime.combine(data, start_time) + duration).time()
            key = (rule.profissional_id, start)
            if key in seen or start <= timezone.now():
                continue
            seen.add(key)
            if not experimental_slot_is_available(servico, rule.profissional, start, end):
                continue
            slots.append({
                'value': f'{rule.profissional_id}|{start.strftime("%Y-%m-%dT%H:%M")}',
                'label': f'{timezone.localtime(start):%H:%M} — {rule.profissional.nome}',
                'professional': rule.profissional,
                'service': servico,
                'start': start,
                'end': end,
            })

    return sorted(slots, key=lambda slot: (slot['start'], slot['professional'].nome))


def experimental_slot_is_available(servico, profissional, inicio, fim, exclude_hold_id=None):
    if (
        inicio >= fim
        or fim - inicio != timedelta(minutes=servico.duracao_minutos)
        or not profissional.ativo
        or not servico.ativo
    ):
        return False

    local_start = timezone.localtime(inicio)
    day_code = DAY_CODES[local_start.weekday()]
    has_rule = RegraDisponibilidade.objects.filter(
        servico=servico,
        profissional=profissional,
        dia_semana__iexact=day_code,
        hora_inicio__lte=local_start.time(),
        hora_fim__gte=timezone.localtime(fim).time(),
    ).exists()
    if not has_rule:
        return False

    if BloqueioAgenda.objects.filter(
        Q(servico__isnull=True) | Q(servico=servico),
        Q(profissional__isnull=True) | Q(profissional=profissional),
        inicio__lt=fim,
        fim__gt=inicio,
    ).exists():
        return False

    appointments = Agendamento.objects.filter(
        profissional=profissional,
        inicio__lt=fim,
        fim__gt=inicio,
        status__in=[Agendamento.STATUS_PENDENTE, Agendamento.STATUS_CONFIRMADO],
    )
    identical_group = appointments.filter(
        servico=servico,
        inicio=inicio,
        fim=fim,
    ).count()
    if appointments.exclude(servico=servico, inicio=inicio, fim=fim).exists():
        return False
    if identical_group >= servico.capacidade_maxima:
        return False

    holds = ReservaHorarioExperimental.objects.filter(
        profissional=profissional,
        inicio__lt=fim,
        fim__gt=inicio,
        expira_em__gt=timezone.now(),
    )
    if exclude_hold_id is not None:
        holds = holds.exclude(pk=exclude_hold_id)
    return not holds.exists()
