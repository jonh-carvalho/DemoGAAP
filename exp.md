# Roteiro da aula experimental GAAP

## Objetivo

Oferecer ao atleta e à família um primeiro contato acolhedor com o GAAP, compreender o que esperam do treinamento e apresentar os próximos passos. Este roteiro é uma sugestão adaptável: a atividade física deve ser definida e conduzida por profissional qualificado, de acordo com o contexto e as condições informadas presencialmente.

## O que o app faz — e o que não faz

- A página pública (`/`) apresenta as frentes do GAAP e recebe pedidos de contato para uma aula experimental de **Treino**.
- O formulário coleta nome do responsável, nome e idade do atleta, WhatsApp, período preferido, e-mail opcional e autorização para contato.
- A solicitação fica com status inicial **Nova** e pode ser acompanhada pela equipe no Django Admin (`/admin/`), onde os status disponíveis são **Nova**, **Em contato**, **Convertida** e **Encerrada**.
- Ao escolher um horário disponível, o envio cria uma reserva temporária de **24 horas**. A aula ainda não está confirmada: a equipe precisa contatar o responsável e aprovar a solicitação.
- A disponibilidade é revalidada ao mostrar horários, ao receber o pedido e novamente na aprovação administrativa. Se a reserva expirar, o horário volta a ficar disponível; a solicitação continua registrada e a equipe deve combinar outra opção com a família.
- A aprovação administrativa cria o responsável, o aluno e um `Agendamento` confirmado. Para isso, a equipe informa a data de nascimento do atleta durante a confirmação; o formulário público continua pedindo apenas a idade e não cria conta de usuário.
- Não solicitar nem registrar dados clínicos no formulário público. Qualquer conversa adicional sobre condições relevantes deve ser feita de forma apropriada pela equipe antes da atividade.

## Preparação da equipe

1. Cadastrar no Admin as regras reais de disponibilidade para Treino em `RegraDisponibilidade`, associando profissional, dia da semana (`MONDAY` a `SUNDAY`) e intervalo de atendimento. Sem regras, a página não oferece horários.
2. Consultar no Admin as novas solicitações e priorizar o retorno conforme o período indicado e o prazo de expiração exibido.
3. Entrar em contato pelo WhatsApp ou e-mail informado, apresentar-se e confirmar se o atleta e, quando aplicável, seu responsável podem comparecer no horário solicitado.
4. Se houver acordo e a reserva ainda estiver válida, usar **Confirmar aula e criar agendamento** no Admin. Informar a data de nascimento correta e confirmar que o horário foi combinado com o responsável. O sistema revalida o horário antes de criar o agendamento.
5. Se o prazo de 24 horas expirou ou o horário deixou de estar disponível, não confirmar a opção antiga: combinar outro horário e orientar o responsável a enviar uma nova solicitação.
6. Antes da atividade, preparar espaço e materiais adequados ao perfil do atleta e combinar quem conduzirá a sessão.
7. Se o atleta for menor de idade, alinhar a presença e participação do responsável. Não presumir que o envio do formulário já significa comparecimento confirmado.

## Sugestão de condução — 60 minutos

| Tempo | Etapa | Condução sugerida |
|---|---|---|
| 0–5 min | Recepção | Cumprimentar atleta e responsável, apresentar o profissional e o espaço. Perguntar como preferem ser chamados e explicar que a sessão será ajustada ao atleta. |
| 5–12 min | Conversa inicial | Perguntar: “O que você gosta de fazer no esporte?”, “O que gostaria de conhecer ou desenvolver?” e “O que espera deste primeiro encontro?”. Ouvir sem prometer resultados. |
| 12–17 min | Orientação | Explicar a sequência da sessão, os limites do espaço e como pedir pausa ou ajuda. Confirmar verbalmente que o atleta está confortável para começar. |
| 17–42 min | Vivência supervisionada | Realizar uma atividade introdutória e lúdica, escolhida pelo profissional conforme idade, experiência e resposta do atleta. Demonstrar, observar e oferecer opções de participação; ajustar ou interromper se houver desconforto. |
| 42–50 min | Encerramento da atividade | Fazer uma transição tranquila para o fim da sessão e perguntar como o atleta se sentiu. Evitar transformar a aula em teste competitivo ou avaliação clínica. |
| 50–60 min | Feedback e próximos passos | Compartilhar observações gerais, ouvir atleta e responsável, explicar as opções de acompanhamento e responder dúvidas. Se houver interesse, alinhar com a equipe como será o próximo contato e a continuidade. |

### Frases úteis

- **Abertura:** “Hoje é para conhecer o espaço, conversar e experimentar uma atividade no seu ritmo.”
- **Durante a vivência:** “Quer tentar assim ou prefere que eu mostre outra opção?”
- **Checagem de conforto:** “Como você está se sentindo? Quer continuar, ajustar ou fazer uma pausa?”
- **Fechamento:** “O que você mais gostou? O que gostaria de saber antes de decidir os próximos passos?”

## Demonstração do fluxo no app

Se a aula experimental também for apresentada como demonstração do sistema, use dados fictícios:

1. Na landing page, mostrar as frentes de atuação, as regras de disponibilidade e o seletor de data e horário.
2. Consultar uma data com disponibilidade e preencher o formulário de exemplo com nome, idade, WhatsApp, período e autorização. Demonstrar a validação do telefone e que a autorização é obrigatória.
3. Enviar e explicar que o horário fica reservado por 24 horas, mas depende de confirmação da equipe.
4. Acessar `/admin/` com uma conta de equipe autorizada, localizar a solicitação e mostrar o prazo da reserva. Após simular o contato com a família, confirmar a solicitação, informar uma data de nascimento compatível com a idade demonstrativa e marcar a confirmação do contato.
5. Mostrar que a solicitação foi convertida e vinculada a um `Agendamento` confirmado. As telas `/agendamentos/` e `/dashboard/` exibem esse agendamento operacional.
6. Se fizer parte da apresentação, mostrar `/servicos/` e `/presencas/` como telas operacionais da equipe.

## Checklist de encerramento

- O atleta e o responsável sabem qual é o próximo passo e quem fará o contato.
- A equipe registrou a evolução da solicitação no Admin.
- Data e horário foram comunicados como confirmados somente depois do contato com a família e da revalidação no Admin.
- Não foram inseridos dados clínicos ou informações pessoais reais na demonstração.
- Feedback e dúvidas foram acolhidos sem prometer resultados esportivos.

## Observações sobre o MVP

- A triagem e confirmação de solicitações experimentais estão disponíveis no Django Admin; o dashboard da equipe não apresenta essa fila.
- O seed não cria regras de disponibilidade: cadastre os dias e horários reais antes de demonstrar ou publicar a consulta de vagas.
- O formulário público usa validação no servidor, exige consentimento para contato e tem um campo honeypot básico. Isso não substitui controles mais completos contra abuso.
- A imagem da landing é provisória e vem de uma URL do Unsplash; antes de publicação, substitua-a por material institucional autorizado do GAAP.
