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
- `ALUNO`: consulta os próprios agendamentos
- `RESPONSAVEL`: consulta e agenda atendimentos dos alunos vinculados

## Interface web

Além da API REST, o projeto oferece páginas Django para acessar os dados pelo navegador. Depois de iniciar o servidor em `http://127.0.0.1:8000/`, estão disponíveis:

- `/`: landing pública do GAAP com apresentação institucional e solicitação de aula experimental
- `/login/`: autenticação da equipe usando as credenciais do sistema
- `/dashboard/`: resumo de usuários, serviços, agendamentos e relatórios
- `/servicos/`: consulta de serviços
- `/agendamentos/`: consulta e gerenciamento de agendamentos
- `/presencas/`: consulta de relatórios e registros relacionados
- `/admin/`: administração e triagem das solicitações experimentais (acesso staff)

### Aula experimental

O formulário público solicita nome do responsável, nome e idade do atleta, WhatsApp, melhor período para contato, e-mail opcional, data e horário disponíveis para uma aula de Treino. É necessário autorizar o contato para enviar o pedido; a autorização e seu horário ficam registrados.

O envio cria uma solicitação independente de `Agendamento` e uma reserva temporária de 24 horas. O horário ainda não está confirmado: a administração deve contatar a família, confirmar o combinado e revalidar a disponibilidade no Django Admin antes de criar o agendamento confirmado. Se a reserva expirar, o horário volta a aparecer como disponível e a solicitação permanece para acompanhamento; a equipe deve combinar outra opção. No momento da confirmação, a equipe informa a data de nascimento do atleta, que é necessária para criar o cadastro de aluno. O fluxo cria os registros de responsável e aluno sem criar conta de usuário.

Os horários são calculados a partir de `RegraDisponibilidade`, da duração e capacidade do serviço, dos agendamentos ativos, dos bloqueios da agenda e das reservas temporárias. Cadastre no Django Admin as regras reais de disponibilidade do serviço Treino, uma por profissional, dia da semana e intervalo, usando códigos como `MONDAY`, `TUESDAY`, `WEDNESDAY`, `THURSDAY`, `FRIDAY`, `SATURDAY` e `SUNDAY`. Sem regras cadastradas, nenhum horário será oferecido. A disponibilidade é revalidada ao exibir opções, ao receber uma solicitação e novamente na confirmação administrativa.

Solicitações experimentais não são expostas por endpoint público. A página usa validação no servidor e um campo honeypot básico contra spam; não solicite nem inclua dados clínicos nesse formulário.

Na landing, a fotografia é carregada de uma URL do Unsplash como imagem provisória de ambiente esportivo. Substitua-a por material institucional autorizado do GAAP antes de publicar o site.

Na página `/agendamentos/`, usuários autorizados podem criar e editar agendamentos, pesquisar e filtrar a lista por data, serviço, profissional e status. O formulário sugere o horário final de acordo com a duração cadastrada no serviço. A ação **Cancelar** altera o status para `CANCELADO`, preservando o histórico em vez de excluir o registro.

As alterações são enviadas aos endpoints REST usando o token JWT obtido no login da interface.

## Dados de demonstração

O comando `python manage.py seed_gaap` cria ou atualiza os dados iniciais sem duplicar os registros principais. Além do administrador e dos usuários originais, são criados estes profissionais de demonstração:

| Usuário | Especialidade | Perfil |
|---|---|---|
| `profissional_educacao_fisica` | Educação Física | `TREINADOR` |
| `fisioterapeuta` | Fisioterapia | `SAUDE` |
| `psicologo` | Psicologia | `SAUDE` |

O seed também disponibiliza os serviços `Treino`, `Fisioterapia`, `Nutricionista` (tipo `NUTRICAO`) e `Psicologia`. As contas criadas pelo seed usam inicialmente a senha `Senha123`; altere-a antes de qualquer uso fora do ambiente local de desenvolvimento.

## Endpoints principais

- `GET /api/v1/usuarios/`
- `GET /api/v1/alunos/`
- `GET /api/v1/responsaveis/`
- `GET /api/v1/servicos/`
- `GET /api/v1/profissionais/`
- `GET /api/v1/agendamentos/`
- `POST /api/v1/agendamentos/` para criar
- `PATCH /api/v1/agendamentos/{id}/` para editar parcialmente
- `DELETE /api/v1/agendamentos/{id}/` para remover via API (a interface web oferece cancelamento lógico)
- `GET /api/v1/bloqueios/`
- `GET /api/docs/` para consultar a documentação OpenAPI/Swagger

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
