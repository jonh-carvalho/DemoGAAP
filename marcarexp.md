# Como marcar uma aula experimental no GAAP

Este roteiro descreve o processo desde a consulta pública de horários até a confirmação pela administração. O pedido inicial **não confirma a aula**: ele mantém o horário reservado por até 24 horas, enquanto a equipe entra em contato e valida a solicitação.

## 1. Preparação da agenda — equipe GAAP

Antes de divulgar horários, um usuário autorizado deve cadastrar a disponibilidade:

1. Acesse `/admin/` e entre com uma conta da equipe que tenha acesso ao Django Admin.
2. Abra **Regras de disponibilidade** e escolha **Adicionar**.
3. Para cada faixa disponível, informe:
   - **Serviço:** Treino;
   - **Profissional:** profissional que atenderá a aula;
   - **Dia da semana:** dia correspondente;
   - **Horário inicial** e **horário final** da faixa.
4. Salve a regra. Cadastre uma regra para cada combinação de profissional, dia e faixa de horário.

O sistema oferece horários em intervalos da duração configurada no serviço Treino, começando no horário inicial da regra. Por exemplo, uma faixa das 9h às 11h com duração de 60 minutos pode oferecer 9h e 10h. Sem regras cadastradas, a página pública não exibirá opções.

## 2. Solicitar o horário — atleta ou responsável

1. Acesse a página inicial do GAAP (`/`) e vá até **Solicite sua aula experimental**.
2. Selecione a data desejada e clique em **Consultar horários**.
3. Escolha um dos horários exibidos. A lista considera disponibilidade cadastrada, duração/capacidade do serviço, reservas temporárias, agendamentos ativos e bloqueios.
4. Preencha nome do responsável, WhatsApp, nome e idade do atleta, período preferido para contato e, opcionalmente, e-mail.
5. Marque a autorização para o GAAP entrar em contato e envie a solicitação.
6. Leia a mensagem de retorno: o horário fica reservado por até **24 horas**, mas a aula ainda depende da confirmação da equipe.

Se não houver horário adequado, consulte outra data. Não envie informações clínicas pelo formulário.

## 3. Analisar e confirmar — equipe GAAP

1. Acesse `/admin/` e abra **Solicitações experimentais**.
2. Localize a solicitação e confira o horário pedido e o horário limite da reserva.
3. Entre em contato com o responsável pelo telefone ou e-mail informado. Confirme que atleta e responsável podem comparecer na data e no horário selecionados.
4. Se estiverem de acordo e a reserva ainda estiver válida, abra a solicitação e clique em **Confirmar aula e criar agendamento**.
5. Informe a data de nascimento correta do atleta. Ela deve corresponder à idade informada no pedido.
6. Marque a confirmação de que o horário foi combinado com o responsável e envie o formulário.
7. O sistema verifica novamente a disponibilidade. Se estiver tudo válido, cria o responsável, o aluno e o agendamento com status **Confirmado**, vincula o agendamento à solicitação e a marca como **Convertida**.
8. Avise o responsável de que a aula está confirmada. O agendamento poderá ser consultado nas telas operacionais da equipe, como `/agendamentos/` e `/dashboard/`.

## 4. Se não for possível confirmar

- **Reserva expirada:** o horário volta a aparecer como disponível, mas a solicitação continua no Admin. Não confirme o horário antigo; converse com a família e peça que escolha outra opção disponível.
- **Horário ocupado ou bloqueado:** a revalidação impede a confirmação. Combine outro horário e solicite uma nova escolha.
- **Solicitação sem continuidade:** a equipe pode encerrá-la no Admin; isso libera a reserva, se ainda existir.

## Checklist rápido

- [ ] Há regras reais cadastradas para o serviço Treino e seus profissionais.
- [ ] O responsável escolheu um horário mostrado como disponível.
- [ ] A equipe entrou em contato antes de confirmar.
- [ ] A confirmação ocorreu dentro das 24 horas e passou pela revalidação.
- [ ] A data de nascimento informada corresponde à idade do atleta.
- [ ] O responsável recebeu a confirmação final do agendamento.
