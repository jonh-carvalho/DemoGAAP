from django.contrib import admin

from .models import SolicitacaoExperimental

# Register your models here.
admin.site.site_header = "GAAP Admin"
admin.site.site_title = "GAAP Admin Portal"
admin.site.index_title = "GAAP Admin Index"


@admin.register(SolicitacaoExperimental)
class SolicitacaoExperimentalAdmin(admin.ModelAdmin):
	list_display = (
		'nome_atleta',
		'idade_atleta',
		'nome_responsavel',
		'telefone',
		'periodo_preferido',
		'status',
		'created_at',
	)
	list_filter = ('status', 'periodo_preferido', 'created_at')
	search_fields = ('nome_responsavel', 'nome_atleta', 'telefone', 'email')
	readonly_fields = ('modalidade', 'consentimento_em', 'created_at', 'updated_at')
	list_per_page = 30
