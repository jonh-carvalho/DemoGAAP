from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Agendamento,
    Aluno,
    BloqueioAgenda,
    Perfil,
    Profissional,
    RelatorioTreino,
    Responsavel,
    Servico,
    Usuario,
)

User = get_user_model()


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'codigo', 'nome']


class UsuarioSerializer(serializers.ModelSerializer):
    perfil = PerfilSerializer(read_only=True)
    perfil_id = serializers.PrimaryKeyRelatedField(source='perfil', queryset=Perfil.objects.all(), write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'perfil', 'perfil_id', 'password']

    def create(self, validated_data):
        perfil = validated_data.pop('perfil')
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(password=password, perfil=perfil, **validated_data)
        return user


class ResponsavelSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(source='usuario', queryset=Usuario.objects.all(), write_only=True)

    class Meta:
        model = Responsavel
        fields = ['id', 'usuario', 'usuario_id', 'nome', 'telefone', 'email', 'created_at']
        read_only_fields = ['created_at']


class AlunoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(source='usuario', queryset=Usuario.objects.all(), write_only=True)
    responsavel = ResponsavelSerializer(read_only=True)
    responsavel_id = serializers.PrimaryKeyRelatedField(source='responsavel', queryset=Responsavel.objects.all(), write_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'usuario', 'usuario_id', 'nome', 'data_nascimento', 'responsavel', 'responsavel_id']


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = ['id', 'nome', 'tipo', 'duracao_minutos', 'capacidade_maxima', 'ativo']


class ProfissionalSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(source='usuario', queryset=Usuario.objects.all(), write_only=True)

    class Meta:
        model = Profissional
        fields = ['id', 'usuario', 'usuario_id', 'nome', 'especialidade', 'ativo']


class AgendamentoSerializer(serializers.ModelSerializer):
    aluno = AlunoSerializer(read_only=True)
    aluno_id = serializers.PrimaryKeyRelatedField(source='aluno', queryset=Aluno.objects.all(), write_only=True)
    servico = ServicoSerializer(read_only=True)
    servico_id = serializers.PrimaryKeyRelatedField(source='servico', queryset=Servico.objects.all(), write_only=True)
    profissional = ProfissionalSerializer(read_only=True)
    profissional_id = serializers.PrimaryKeyRelatedField(source='profissional', queryset=Profissional.objects.all(), write_only=True)
    created_by = UsuarioSerializer(read_only=True)

    class Meta:
        model = Agendamento
        fields = [
            'id',
            'aluno',
            'aluno_id',
            'servico',
            'servico_id',
            'profissional',
            'profissional_id',
            'inicio',
            'fim',
            'status',
            'presenca',
            'observacoes',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class BloqueioAgendaSerializer(serializers.ModelSerializer):
    created_by = UsuarioSerializer(read_only=True)

    class Meta:
        model = BloqueioAgenda
        fields = ['id', 'servico', 'profissional', 'inicio', 'fim', 'motivo', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class RelatorioTreinoSerializer(serializers.ModelSerializer):
    agendamento = AgendamentoSerializer(read_only=True)
    agendamento_id = serializers.PrimaryKeyRelatedField(source='agendamento', queryset=Agendamento.objects.all(), write_only=True)
    created_by = UsuarioSerializer(read_only=True)

    class Meta:
        model = RelatorioTreino
        fields = ['id', 'agendamento', 'agendamento_id', 'titulo', 'conteudo', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)
