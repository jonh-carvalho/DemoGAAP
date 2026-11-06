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

## Teste temporário no Railway

Esta configuração é somente para demonstração com dados fictícios. Não use dados reais: o SQLite fica em `/tmp/gaap.sqlite3` e pode ser perdido ao reiniciar, recriar ou atualizar o serviço. O banco versionado não é utilizado. Não configure réplicas, pois cada uma teria seu próprio banco. O SQLite também não é adequado para validar a concorrência dos agendamentos em produção.

1. Verifique o conteúdo de `db.sqlite3` antes de enviar o repositório ao Railway: ele está versionado e pode ser incluído no código implantado, embora não seja o banco usado pela aplicação. Se contiver dados sensíveis, não faça o deploy até removê-los do repositório e tratar a exposição. Envie as alterações ao GitHub e crie um serviço no Railway a partir do repositório. Não adicione banco de dados nem volume.
2. Em **Settings → Networking → Public Networking**, gere um domínio. Em **Variables**, configure:
   - `DJANGO_SETTINGS_MODULE`: `gaap_backend.railway_settings`
   - `SECRET_KEY`: uma chave aleatória exclusiva para este ambiente. Por exemplo, gere uma localmente com `python -c "import secrets; print(secrets.token_urlsafe(64))"` e copie o resultado para o Railway.
   - `ALLOWED_HOSTS`: o domínio gerado, sem `https://` (por exemplo, `exemplo.up.railway.app`).
   - `CSRF_TRUSTED_ORIGINS`: a URL HTTPS completa do domínio (por exemplo, `https://exemplo.up.railway.app`).

   As configurações de teste usam `DEBUG=False` e não leem as sugestões de `DEBUG` ou `DATABASE_URL` do `.env.example`. Não publique a chave no repositório.
3. Em **Settings → Deploy → Start Command**, configure:

   ```sh
   /bin/sh -c 'python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn gaap_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4'
   ```

   As migrações rodam no próprio serviço, onde o SQLite é criado. As threads permitem que as páginas façam chamadas HTTP à API no mesmo serviço; esta configuração é destinada apenas a um teste com poucos acessos.
4. Aplique as alterações e acompanhe os logs do deploy. Abra a URL gerada e verifique a página inicial e `/admin/`.
5. Para testar com acesso administrativo, conecte-se ao serviço em execução usando a [CLI e o SSH do Railway](https://docs.railway.com/cli/ssh) e execute `python manage.py createsuperuser`. Escolha uma senha forte. Depois, no mesmo serviço, execute `python manage.py shell` e atribua o perfil necessário para acessar a API:

   ```python
   from django.contrib.auth import get_user_model
   from gaap.models import Perfil
   perfil, _ = Perfil.objects.get_or_create(codigo='ADMIN', defaults={'nome': 'Administrador'})
   usuario = get_user_model().objects.get(username='NOME_DO_SUPERUSUARIO')
   usuario.perfil = perfil
   usuario.save(update_fields=['perfil'])
   ```

   Substitua `NOME_DO_SUPERUSUARIO` pelo nome escolhido. Crie os serviços, profissionais e regras de disponibilidade no Admin para testar aulas experimentais. Não execute `seed_gaap` em um ambiente público: ele define senhas de demonstração conhecidas. Quando o banco for perdido, será necessário refazer esses cadastros.

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
