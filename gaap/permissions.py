from rest_framework.permissions import BasePermission


class PerfilRequired(BasePermission):
    allowed_codes = set()
    message = 'Seu perfil não tem acesso a esta operação.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        perfil = getattr(user, 'perfil', None)
        return bool(user and user.is_authenticated and perfil and perfil.codigo in self.allowed_codes)


class IsAdmin(PerfilRequired):
    allowed_codes = {'ADMIN'}
    message = 'Acesso permitido apenas para administradores.'


class IsTreinador(PerfilRequired):
    allowed_codes = {'TREINADOR'}
    message = 'Acesso permitido apenas para treinadores.'


class IsProfissionalSaude(PerfilRequired):
    allowed_codes = {'SAUDE'}
    message = 'Acesso permitido apenas para profissionais de saúde.'


class IsAdminOrTreinador(PerfilRequired):
    allowed_codes = {'ADMIN', 'TREINADOR'}
    message = 'Acesso permitido apenas para administradores e treinadores.'


class IsAluno(PerfilRequired):
    allowed_codes = {'ALUNO'}
    message = 'Acesso permitido apenas para alunos.'


class IsResponsavel(PerfilRequired):
    allowed_codes = {'RESPONSAVEL'}
    message = 'Acesso permitido apenas para responsáveis.'


class IsAlunoOrResponsavel(PerfilRequired):
    allowed_codes = {'ALUNO', 'RESPONSAVEL'}
    message = 'Acesso permitido apenas para alunos e responsáveis.'
