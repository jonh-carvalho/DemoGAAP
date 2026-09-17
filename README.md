# GAAP Backend

Backend do MVP do GAAP (Gestão de Atletas de Alta Performance) para apoiar agendamento, agenda, presença e relatórios operacionais.

## Tecnologias

- Python 3.13+
- Django 6.1
- Django REST Framework
- JWT via Simple JWT
- SQLite para desenvolvimento
- pytest + pytest-django

## Estrutura do projeto

- `gaap/`: modelos, serializers, views, permissões e comandos de seed
- `gaap_backend/`: configuração principal do projeto
- `docs/uml/`: diagramas PlantUML

## Instalação

1. Crie e ative o ambiente virtual
   ```bash
   python -m venv .venv
   . .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate # Windows PowerShell
   ```

2. Instale as dependências
   ```bash
   pip install -r requirements.txt
   ```

3. Aplique as migrações
   ```bash
   python manage.py migrate
   ```

4. Crie usuários e dados iniciais
   ```bash
   python manage.py seed_gaap
   ```

5. Execute a API
   ```bash
   python manage.py runserver
   ```

## Autenticação

A API usa JWT com endpoints:

- `POST /api/v1/auth/token/` para obter tokens
- `POST /api/v1/auth/token/refresh/` para atualizar token

Exemplo de payload:

```json
{
  "username": "admin",
  "password": "Senha123"
}
```

## Perfis principais

- `ADMIN`: gestão operacional completa
- `TREINADOR`: agenda e relatórios de treino
- `SAUDE`: agenda e atendimento de saúde

## Endpoints principais

- `GET /api/v1/usuarios/`
- `GET /api/v1/alunos/`
- `GET /api/v1/responsaveis/`
- `GET /api/v1/servicos/`
- `GET /api/v1/profissionais/`
- `GET /api/v1/agendamentos/`
- `GET /api/v1/bloqueios/`

## Regras de negócio implementadas

- aluno não pode ter agenda sobreposta
- profissional não pode atender em intervalos sobrepostos
- capacidade máxima por serviço não pode ser excedida
- agendamento em horário bloqueado é rejeitado
- autorização por perfil aplicada no servidor

## Testes

```bash
pytest -q
```

## Diagramas UML

Os diagramas PlantUML estão em `docs/uml/` e cobrem:

- casos de uso
- modelo de classes
- sequência de confirmação de agendamento
- fluxo de atividades
- modelo entidade-relacionamento

## Observações

Este é um MVP acadêmico focado em agenda, capacidade e operação de treino; módulos financeiros, BI, mobile e PDF ficam fora do escopo desta entrega.
