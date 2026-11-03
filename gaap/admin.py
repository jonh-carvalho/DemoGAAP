from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone

from .booking import confirmar_solicitacao_experimental
from .forms import ConfirmarAulaExperimentalForm
from .models import ReservaHorarioExperimental, RegraDisponibilidade, SolicitacaoExperimental


admin.site.site_header = 'GAAP Admin'
admin.site.site_title = 'GAAP Admin Portal'
admin.site.index_title = 'GAAP Admin Index'


@admin.register(RegraDisponibilidade)
class RegraDisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ('servico', 'profissional', 'dia_semana', 'hora_inicio', 'hora_fim')
    list_filter = ('servico', 'profissional', 'dia_semana')
    ordering = ('dia_semana', 'hora_inicio')
    fields = ('servico', 'profissional', 'dia_semana', 'hora_inicio', 'hora_fim')


@admin.register(SolicitacaoExperimental)
class SolicitacaoExperimentalAdmin(admin.ModelAdmin):
    change_form_template = 'admin/gaap/solicitacaoexperimental/change_form.html'
    list_display = (
        'nome_atleta',
        'idade_atleta',
        'nome_responsavel',
        'telefone',
        'periodo_preferido',
        'horario_solicitado',
        'reserva_ate',
        'status',
        'created_at',
    )
    list_filter = ('status', 'periodo_preferido', 'created_at')
    search_fields = ('nome_responsavel', 'nome_atleta', 'telefone', 'email')
    readonly_fields = (
        'modalidade',
        'profissional_solicitado',
        'inicio_solicitado',
        'agendamento',
        'consentimento_em',
        'created_at',
        'updated_at',
        'status',
    )
    actions = ('marcar_em_contato', 'encerrar_solicitacoes')
    list_per_page = 30

    @admin.display(description='Horário solicitado')
    def horario_solicitado(self, obj):
        if not obj.inicio_solicitado:
            return '-'
        return timezone.localtime(obj.inicio_solicitado).strftime('%d/%m/%Y %H:%M')

    @admin.display(description='Reserva até')
    def reserva_ate(self, obj):
        try:
            return timezone.localtime(obj.reserva_horario.expira_em).strftime('%d/%m/%Y %H:%M')
        except ReservaHorarioExperimental.DoesNotExist:
            return '-'

    @admin.action(description='Marcar solicitações selecionadas como em contato')
    def marcar_em_contato(self, request, queryset):
        queryset.filter(status=SolicitacaoExperimental.STATUS_NOVA).update(
            status=SolicitacaoExperimental.STATUS_EM_CONTATO
        )

    @admin.action(description='Encerrar solicitações selecionadas e liberar horários')
    def encerrar_solicitacoes(self, request, queryset):
        for solicitacao in queryset:
            if solicitacao.status in {
                SolicitacaoExperimental.STATUS_NOVA,
                SolicitacaoExperimental.STATUS_EM_CONTATO,
            }:
                ReservaHorarioExperimental.objects.filter(solicitacao=solicitacao).delete()
                solicitacao.status = SolicitacaoExperimental.STATUS_ENCERRADA
                solicitacao.save(update_fields=['status', 'updated_at'])

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/confirmar-aula/',
                self.admin_site.admin_view(self.confirmar_aula),
                name='gaap_solicitacaoexperimental_confirmar',
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['confirm_url'] = reverse(
            'admin:gaap_solicitacaoexperimental_confirmar',
            args=[object_id],
        )
        return super().change_view(request, object_id, form_url, extra_context)

    def confirmar_aula(self, request, object_id):
        solicitacao = get_object_or_404(SolicitacaoExperimental, pk=object_id)
        if solicitacao.status == SolicitacaoExperimental.STATUS_CONVERTIDA:
            self.message_user(request, 'Esta solicitação já foi convertida.', level=messages.WARNING)
            return redirect('admin:gaap_solicitacaoexperimental_change', object_id)

        if request.method == 'POST':
            form = ConfirmarAulaExperimentalForm(request.POST, solicitacao=solicitacao)
            if form.is_valid():
                try:
                    confirmar_solicitacao_experimental(
                        solicitacao.pk,
                        request.user,
                        form.cleaned_data['data_nascimento'],
                    )
                except ValidationError as exc:
                    form.add_error(None, exc)
                else:
                    self.message_user(
                        request,
                        'A aula experimental foi confirmada e o agendamento foi criado.',
                        level=messages.SUCCESS,
                    )
                    return redirect('admin:gaap_solicitacaoexperimental_change', object_id)
        else:
            form = ConfirmarAulaExperimentalForm(solicitacao=solicitacao)

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'original': solicitacao,
            'title': 'Confirmar aula experimental',
            'form': form,
            'cancel_url': reverse('admin:gaap_solicitacaoexperimental_change', args=[object_id]),
        }
        return render(
            request,
            'admin/gaap/solicitacaoexperimental/confirmar_aula.html',
            context,
        )
