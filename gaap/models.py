from datetime import timezone as dt_timezone

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Perfil(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    perfil = models.ForeignKey(Perfil, on_delete=models.PROTECT, related_name='usuarios', null=True, blank=True)

    def __str__(self):
        return self.username


class Responsavel(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name='responsavel', null=True, blank=True)
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['telefone'])]

    def __str__(self):
        return self.nome


class Aluno(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name='aluno', null=True, blank=True)
    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    responsavel = models.ForeignKey(Responsavel, on_delete=models.PROTECT, related_name='alunos')

    def __str__(self):
        return self.nome


class Servico(models.Model):
    TIPO_TREINO = 'TREINO'
    TIPO_FISIOTERAPIA = 'FISIOTERAPIA'
    TIPO_PSICOLOGIA = 'PSICOLOGIA'
    TIPO_NUTRICAO = 'NUTRICAO'
    TIPOS = [
        (TIPO_TREINO, 'Treino'),
        (TIPO_FISIOTERAPIA, 'Fisioterapia'),
        (TIPO_PSICOLOGIA, 'Psicologia'),
        (TIPO_NUTRICAO, 'Nutrição'),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=30, choices=TIPOS)
    duracao_minutos = models.PositiveIntegerField(default=60)
    capacidade_maxima = models.PositiveIntegerField(default=1)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Profissional(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.PROTECT, related_name='profissional')
    nome = models.CharField(max_length=150)
    especialidade = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class RegraDisponibilidade(models.Model):
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='regras_disponibilidade')
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='regras_disponibilidade')
    dia_semana = models.CharField(max_length=20)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    class Meta:
        unique_together = ('servico', 'profissional', 'dia_semana', 'hora_inicio', 'hora_fim')


class BloqueioAgenda(models.Model):
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='bloqueios', null=True, blank=True)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='bloqueios', null=True, blank=True)
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    motivo = models.CharField(max_length=255)
    created_by = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='bloqueios_criados')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['inicio', 'fim'])]

    def clean(self):
        super().clean()
        if self.inicio >= self.fim:
            raise ValidationError('A data final deve ser maior que a inicial.')


class Agendamento(models.Model):
    STATUS_PENDENTE = 'PENDENTE'
    STATUS_CONFIRMADO = 'CONFIRMADO'
    STATUS_CANCELADO = 'CANCELADO'
    STATUS_REALIZADO = 'REALIZADO'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_CONFIRMADO, 'Confirmado'),
        (STATUS_CANCELADO, 'Cancelado'),
        (STATUS_REALIZADO, 'Realizado'),
    ]

    PRESENCA_PENDENTE = 'PENDENTE'
    PRESENCA_PRESENTE = 'PRESENTE'
    PRESENCA_FALTA = 'FALTA'
    PRESENCA_CHOICES = [
        (PRESENCA_PENDENTE, 'Pendente'),
        (PRESENCA_PRESENTE, 'Presente'),
        (PRESENCA_FALTA, 'Falta'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    profissional = models.ForeignKey(Profissional, on_delete=models.PROTECT, related_name='agendamentos')
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    presenca = models.CharField(max_length=20, choices=PRESENCA_CHOICES, default=PRESENCA_PENDENTE)
    observacoes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='agendamentos_criados')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['inicio', 'fim']), models.Index(fields=['status'])]

    def clean(self):
        super().clean()
        if self.inicio >= self.fim:
            raise ValidationError('A data final deve ser maior que a inicial.')

        if self.status in {self.STATUS_PENDENTE, self.STATUS_CONFIRMADO}:
            self._validar_capacidade()
            self._validar_conflitos_aluno()
            self._validar_conflitos_profissional()
            self._validar_bloqueios()

    def _validar_bloqueios(self):
        bloqueios = BloqueioAgenda.objects.filter(
            Q(servico=self.servico, profissional=self.profissional) | Q(servico=self.servico) | Q(profissional=self.profissional)
        )
        for bloqueio in bloqueios:
            if self.inicio < bloqueio.fim and self.fim > bloqueio.inicio:
                raise ValidationError('Não é possível confirmar agendamento em horário bloqueado.')

    def _validar_capacidade(self):
        agendamentos = Agendamento.objects.filter(
            servico=self.servico,
            profissional=self.profissional,
            inicio__lt=self.fim,
            fim__gt=self.inicio,
            status__in=[self.STATUS_CONFIRMADO, self.STATUS_PENDENTE]
        ).exclude(pk=self.pk)
        qtd = agendamentos.count() + 1
        if qtd > self.servico.capacidade_maxima:
            raise ValidationError('Capacidade do serviço excedida para este horário.')

    def _validar_conflitos_aluno(self):
        conflitos = Agendamento.objects.filter(
            aluno=self.aluno,
            inicio__lt=self.fim,
            fim__gt=self.inicio,
            status__in=[self.STATUS_CONFIRMADO, self.STATUS_PENDENTE]
        ).exclude(pk=self.pk)
        if conflitos.exists():
            raise ValidationError('O aluno já possui outro agendamento ativo sobreposto.')

    def pode_ser_visto_por(self, usuario):
        if not usuario or not getattr(usuario, 'is_authenticated', False):
            return False
        perfil = getattr(usuario, 'perfil', None)
        if perfil and perfil.codigo in {'ADMIN', 'TREINADOR', 'SAUDE'}:
            return True
        return (
            self.aluno.usuario_id == usuario.id
            or self.aluno.responsavel.usuario_id == usuario.id
        )

    def _validar_conflitos_profissional(self):
        conflitos = Agendamento.objects.filter(
            profissional=self.profissional,
            inicio__lt=self.fim,
            fim__gt=self.inicio,
            status__in=[self.STATUS_CONFIRMADO, self.STATUS_PENDENTE]
        ).exclude(pk=self.pk)

        for conflito in conflitos:
            mesmo_turno_grupo = (
                conflito.servico_id == self.servico_id
                and self._normalizar_data(conflito.inicio) == self._normalizar_data(self.inicio)
                and self._normalizar_data(conflito.fim) == self._normalizar_data(self.fim)
            )
            if not mesmo_turno_grupo:
                raise ValidationError('O profissional não pode atender agendamentos sobrepostos.')

    @staticmethod
    def _normalizar_data(value):
        if timezone.is_aware(value):
            return value.astimezone(dt_timezone.utc).replace(tzinfo=None)
        return value

    def registrar_presenca(self, valor, usuario):
        if valor not in {self.PRESENCA_PRESENTE, self.PRESENCA_FALTA}:
            raise ValidationError('Presença inválida.')
        self.presenca = valor
        self.updated_at = timezone.now()
        self.save(update_fields=['presenca', 'updated_at'])

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class RelatorioTreino(models.Model):
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE, related_name='relatorios')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    created_by = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='relatorios_criados')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class SolicitacaoExperimental(models.Model):
    STATUS_NOVA = 'NOVA'
    STATUS_EM_CONTATO = 'EM_CONTATO'
    STATUS_CONVERTIDA = 'CONVERTIDA'
    STATUS_ENCERRADA = 'ENCERRADA'
    STATUS_CHOICES = [
        (STATUS_NOVA, 'Nova'),
        (STATUS_EM_CONTATO, 'Em contato'),
        (STATUS_CONVERTIDA, 'Convertida'),
        (STATUS_ENCERRADA, 'Encerrada'),
    ]
    PERIODO_MANHA = 'MANHA'
    PERIODO_TARDE = 'TARDE'
    PERIODO_NOITE = 'NOITE'
    PERIODO_FLEXIVEL = 'FLEXIVEL'
    PERIODO_CHOICES = [
        (PERIODO_MANHA, 'Manhã'),
        (PERIODO_TARDE, 'Tarde'),
        (PERIODO_NOITE, 'Noite'),
        (PERIODO_FLEXIVEL, 'Flexível'),
    ]

    nome_responsavel = models.CharField(max_length=150)
    nome_atleta = models.CharField(max_length=150)
    idade_atleta = models.PositiveSmallIntegerField()
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    periodo_preferido = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    modalidade = models.CharField(max_length=20, default='TREINO', editable=False)
    consentimento_contato = models.BooleanField(default=False)
    consentimento_em = models.DateTimeField(null=True, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOVA)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'created_at'])]

    def __str__(self):
        return f'{self.nome_atleta} - {self.get_status_display()}'
