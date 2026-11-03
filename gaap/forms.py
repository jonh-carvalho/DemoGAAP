import re
from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.dateparse import parse_date
from django.utils import timezone

from .availability import available_experimental_slots, experimental_slot_is_available
from .models import Profissional, ReservaHorarioExperimental, SolicitacaoExperimental


class SolicitacaoExperimentalForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    data_aula = forms.DateField(
        required=True,
        label='Data desejada',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    horario = forms.ChoiceField(required=True, label='Horário disponível')
    consentimento_contato = forms.BooleanField(
        required=True,
        error_messages={'required': 'Precisamos da sua autorização para entrar em contato.'},
        label='Autorizo o GAAP a entrar em contato sobre esta solicitação.',
    )

    class Meta:
        model = SolicitacaoExperimental
        fields = [
            'nome_responsavel',
            'nome_atleta',
            'idade_atleta',
            'telefone',
            'email',
            'periodo_preferido',
            'consentimento_contato',
        ]
        widgets = {
            'nome_responsavel': forms.TextInput(attrs={'autocomplete': 'name', 'maxlength': 150}),
            'nome_atleta': forms.TextInput(attrs={'maxlength': 150}),
            'idade_atleta': forms.NumberInput(attrs={'min': 3, 'max': 100}),
            'telefone': forms.TelInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel', 'maxlength': 24}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'periodo_preferido': forms.Select(),
        }
        labels = {
            'nome_responsavel': 'Seu nome',
            'nome_atleta': 'Nome do atleta',
            'idade_atleta': 'Idade do atleta',
            'telefone': 'WhatsApp',
            'email': 'E-mail (opcional)',
            'periodo_preferido': 'Melhor período para contato',
        }
        error_messages = {
            'idade_atleta': {'required': 'Informe a idade do atleta.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['periodo_preferido'].choices = [
            ('', 'Selecione um período'),
            *SolicitacaoExperimental.PERIODO_CHOICES,
        ]
        raw_date = self.data.get('data_aula') if self.is_bound else self.initial.get('data_aula')
        self.availability_date = parse_date(str(raw_date)) if raw_date else None
        self.available_slots = (
            available_experimental_slots(self.availability_date)
            if self.availability_date
            else []
        )
        choices = [('', 'Selecione uma data para ver os horários')]
        choices.extend((slot['value'], slot['label']) for slot in self.available_slots)
        posted_slot = self.data.get('horario') if self.is_bound else None
        if posted_slot and posted_slot not in {value for value, _ in choices}:
            choices.append((posted_slot, 'Este horário não está mais disponível'))
        self.fields['horario'].choices = choices

    def clean_website(self):
        website = self.cleaned_data.get('website', '').strip()
        if website:
            raise forms.ValidationError('Não foi possível enviar a solicitação.')
        return website

    def clean_idade_atleta(self):
        idade = self.cleaned_data['idade_atleta']
        if idade < 3 or idade > 100:
            raise forms.ValidationError('Informe uma idade entre 3 e 100 anos.')
        return idade

    def clean_telefone(self):
        telefone = re.sub(r'\D', '', self.cleaned_data['telefone'])
        nacional = telefone[2:] if telefone.startswith('55') and len(telefone) in {12, 13} else telefone
        if len(nacional) not in {10, 11}:
            raise forms.ValidationError('Informe um telefone com DDD e 10 ou 11 dígitos.')
        return telefone

    def clean_horario(self):
        horario = self.cleaned_data['horario']
        slot = next((slot for slot in self.available_slots if slot['value'] == horario), None)
        if slot is None:
            raise forms.ValidationError(
                'Esse horário não está mais disponível. Consulte novamente os horários.'
            )
        self.selected_slot = slot
        return horario

    def clean(self):
        cleaned_data = super().clean()
        data_aula = cleaned_data.get('data_aula')
        slot = getattr(self, 'selected_slot', None)
        if data_aula and slot and not experimental_slot_is_available(
            slot['service'],
            slot['professional'],
            slot['start'],
            slot['end'],
        ):
            self.add_error('horario', 'Esse horário acabou de ser solicitado. Escolha outro.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.consentimento_contato and not instance.consentimento_em:
            instance.consentimento_em = timezone.now()
        slot = self.selected_slot
        instance.profissional_solicitado = slot['professional']
        instance.inicio_solicitado = slot['start']
        if not commit:
            return instance
        try:
            with transaction.atomic():
                Profissional.objects.select_for_update().get(pk=slot['professional'].pk)
                if not experimental_slot_is_available(
                    slot['service'],
                    slot['professional'],
                    slot['start'],
                    slot['end'],
                ):
                    raise ValidationError('Esse horário acabou de ser solicitado. Escolha outro.')
                instance.save()
                ReservaHorarioExperimental.objects.create(
                    solicitacao=instance,
                    profissional=slot['professional'],
                    inicio=slot['start'],
                    fim=slot['end'],
                    expira_em=timezone.now() + timedelta(hours=24),
                )
        except IntegrityError as exc:
            cause = exc.__cause__
            constraint = getattr(getattr(cause, 'diag', None), 'constraint_name', None)
            message = str(cause or exc)
            if (
                constraint == 'unique_experimental_hold_professional_start'
                or 'gaap_reservahorarioexperimental.profissional_id' in message
            ):
                raise ValidationError(
                    'Esse horário acabou de ser solicitado. Escolha outro.'
                ) from exc
            raise
        return instance


class ConfirmarAulaExperimentalForm(forms.Form):
    data_nascimento = forms.DateField(
        label='Data de nascimento do atleta',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    contato_confirmado = forms.BooleanField(
        required=True,
        label='Confirmei com o responsável que o horário solicitado está confirmado.',
    )

    def __init__(self, *args, solicitacao, **kwargs):
        self.solicitacao = solicitacao
        super().__init__(*args, **kwargs)

    def clean_data_nascimento(self):
        data_nascimento = self.cleaned_data['data_nascimento']
        hoje = timezone.localdate()
        idade = hoje.year - data_nascimento.year - (
            (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
        )
        if idade != self.solicitacao.idade_atleta:
            raise forms.ValidationError(
                'A data de nascimento não corresponde à idade informada na solicitação.'
            )
        return data_nascimento
