# Cenário de Aula: Backend GAAP

## 1. Contexto e desafio

Uma escola de treinamento esportivo precisa organizar alunos, profissionais e sessões de Treino, Fisioterapia, Psicologia e Nutrição. Atualmente, a operação depende de controles dispersos e não possui uma fonte confiável para acompanhar vagas, presenças e relatórios de treino.

A turma deverá projetar e entregar, em quatro meses, o backend de um recorte inicial do GAAP (Gestão de Atletas de Alta Performance). A proposta parte da análise do ambiente PKZ & One to One, mas o produto acadêmico não deve tentar reproduzir todos os módulos clínicos, financeiros, de BI ou mobile observados. O foco é entregar uma API funcional, testada e documentada para sustentar a operação de agenda e treino.

## 2. Objetivos pedagógicos

- Aplicar programação orientada a objetos na modelagem das regras do domínio.
- Projetar um banco de dados relacional normalizado e implementar persistência com ORM.
- Produzir e manter diagramas UML de casos de uso, classes e sequência.
- Construir uma API REST com validação, tratamento de erros, autenticação e autorização por perfil.
- Trabalhar de forma iterativa com RUP/UP, Git, GitHub Issues, pull requests e GitHub Projects.

## 3. Escopo do MVP

### Perfis de usuário

| Perfil | Responsabilidades iniciais |
|---|---|
| Administrador | Mantém usuários, alunos, responsáveis, profissionais, serviços, horários e bloqueios; consulta pendências. |
| Treinador | Consulta a agenda sob sua responsabilidade, registra presença/falta e cria relatórios de treino. |
| Profissional de saúde | Consulta apenas os atendimentos atribuídos ao seu serviço e agenda. |
| Aluno | Consulta apenas seus agendamentos e perfil pessoal. |
| Responsável | Consulta e agenda os atendimentos do aluno sob sua responsabilidade. |

### Funcionalidades iniciais

1. Autenticação de usuários e autorização por perfil.
2. Cadastro e consulta de alunos, profissionais e serviços.
3. Configuração de horários, capacidade e bloqueios de agenda por serviço.
4. Agendamento de aluno em um serviço e horário disponível.
5. Consulta de agenda por data, serviço e profissional.
6. Busca de alunos por nome ou telefone do responsável.
7. Fluxo de Caixaledger financeiro: Receitas e Despesas

### Fora do escopo desta entrega

- Pagamentos, gateway, cobrança recorrente 
- Prontuário clínico detalhado, assinatura digital e cálculos de força por sexo e idade.
- Aplicativo mobile, QR Code, notificações por WhatsApp/e-mail e operação offline.
- Dashboards analíticos, data warehouse, multi-tenancy e integrações públicas.
- Geração de PDF e upload de fotos; a API deve deixar pontos de extensão documentados para essas evoluções.

## 4. Modelo inicial do domínio

As entidades mínimas são `Usuario`, `Perfil`, `Aluno`, `Responsavel`, `Servico`, `Profissional`, `RegraDisponibilidade`, `BloqueioAgenda`, `Agendamento`.

A regra de modelo foi ampliada para refletir quem participa do sistema: `Aluno` e `Responsavel` passam a possuir vínculo direto com `Usuario`, permitindo autenticação individual e visibilidade controlada. `Aluno` pode somente consultar seus agendamentos; `Responsavel` pode consultar e agendar os atendimentos do aluno sob sua responsabilidade. O banco relacional deve usar chaves primárias, chaves estrangeiras, restrições de unicidade e índices para consultas de agenda. A equipe deve justificar as cardinalidades no diagrama de classes e no diagrama entidade-relacionamento. Dados de autenticação não devem ser armazenados em texto puro; senhas devem ser protegidas por hash.

## 5. Regras de negócio prioritárias

| ID | Regra |
|---|---|
| RN01 | Um agendamento deve referenciar um aluno, um serviço, um profissional, uma data/hora e um status. |
| RN02 | O sistema não pode confirmar agendamento em horário bloqueado, encerrado ou que tenha atingido a capacidade do serviço. |
| RN03 | Para o MVP, Treino tem duração de 60 minutos e capacidade máxima de 6 alunos; Fisioterapia tem 30 minutos e capacidade 1; Psicologia e Nutrição têm 30 minutos e capacidade 1. Essas regras devem ser parametrizadas no cadastro do serviço. |
| RN04 | Um aluno não pode ter dois agendamentos ativos que se sobreponham no tempo. |
| RN05 | Um profissional não pode atender dois agendamentos sobrepostos. |
| RN06 | Somente administrador pode criar bloqueios, manter horários e cadastrar usuários. |
| RN07 | A visualização deve respeitar o perfil: treinador, profissional, aluno e responsável veem somente os registros permitidos; administrador possui visão operacional completa. |
| RN08 | Aluno pode consultar apenas seus próprios agendamentos; responsável pode consultar e criar agendamentos para o aluno sob sua responsabilidade. |
| RN09 | A busca de aluno deve aceitar nome ou telefone do responsável e retornar somente dados permitidos ao perfil autenticado. |
| RN10 | Alterações críticas de agenda, presença e relatório devem registrar autor, data/hora e valores essenciais para auditoria. |

## 6. Requisitos não funcionais

- API REST em JSON, com rotas versionadas, por exemplo, `/api/v1/agendamentos`.
- Validação de entrada e respostas de erro padronizadas.
- Autenticação por JWT token; autorização aplicada no servidor.
- Cobertura de testes para todas as regras RN01 a RN10 e para os principais fluxos de API.
- Documentação de instalação, variáveis de ambiente, modelo de dados, endpoints e decisões arquiteturais.



## 8. Artefatos UML obrigatórios

1. Diagrama de casos de uso com os três perfis e os casos prioritários.
2. Diagrama de classes do domínio, com atributos relevantes, associações, multiplicidades e responsabilidades.
3. Diagrama de sequência para o caso "Confirmar agendamento", evidenciando validação de capacidade, conflito e bloqueio.
4. Diagrama de atividades para representar o fluxo de trabalho dos principais processos.
5. Diagrama entidade-relacionamento compatível com as migrações implementadas.

Os diagramas devem ser versionados no repositório e atualizados sempre que uma decisão de modelagem mudar.

## 9. Ferramentas e tecnologias sugeridas

- Linguagem de programação: Python
- Framework web: Django REST Framework com Django ORM
- Banco de dados: Produção: PostgreSQL; Desenvolvimento: SQLite
- Uso do PlantUML para diagramas

## 10. Status da implementação atual

- O backend foi implementado em Django REST Framework com autenticação por JWT, autorização por perfil e regras de domínio no modelo de agendamento.
- `Aluno` e `Responsavel` passam a ter vínculo direto com `Usuario`, permitindo autenticação individual e controle de visibilidade por perfil.
- `Aluno` pode consultar apenas os próprios agendamentos; `Responsavel` pode consultar e agendar atendimentos do aluno sob sua responsabilidade.
- A regra de sobreposição foi validada para impedir conflitos de aluno e profissional, com suporte a grupos que compartilham o mesmo turno quando o serviço e o intervalo forem iguais.
- A funcionalidade de presença e relatórios de treino foi adicionada e validada, com a migração correspondente aplicada no banco SQLite de desenvolvimento.
- Foi adicionada uma camada de páginas Django para acessar os endpoints em navegador, com login, dashboard, listagens de serviços, agendamentos e relatórios/presenças.
- Estado atual verificado: `System check identified no issues (0 silenced)` e `7 passed in 14.33s`.