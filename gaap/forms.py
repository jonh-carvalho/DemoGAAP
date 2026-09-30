import re

from django import forms
from django.utils import timezone

from .models import SolicitacaoExperimental


class SolicitacaoExperimentalForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.consentimento_contato and not instance.consentimento_em:
            instance.consentimento_em = timezone.now()
        if commit:
            instance.save()
        return instance
