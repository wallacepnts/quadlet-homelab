# Radicale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor CalDAV/CardDAV leve e minimalista.

## Primeiro acesso

Abrir `http://<ip-do-host>:5232` ou `https://radicale.<your-tailnet>.ts.net`.

## Arquivos

```
radicale.container   unit
.env.example         ambiente
config/config        a config do Radicale, para dentro do volume
birthday-sync/       o timer e o service dele, para o systemd/user
install.ini
```

## Calendário de aniversários

Um timer lê as datas de nascimento dos seus contatos e mantém um calendário
chamado `birthdays` em dia com elas, então contato novo vira evento anual sem
você digitar duas vezes.

O script que faz isso vem dentro da imagem — ela é um rebuild do
`tomsquest/docker-radicale` que o carrega, porque o script importa `vobject` e
`dateutil`, e a imagem oficial não tem nenhum dos dois. Instalar em tempo de
execução também não dá: este container é `ReadOnly=true`.

A instalação coloca o timer no lugar; habilitar é um comando, uma vez:

```bash
systemctl --user enable --now radicale-birthday-sync.timer
```

Ele roda 5 minutos depois do boot e a cada 30 minutos. Para conferir:

```bash
systemctl --user list-timers radicale-birthday-sync.timer
journalctl --user -u radicale-birthday-sync.service -n 20
```

O calendário `birthdays` é criado na primeira execução, na coleção de cada
usuário. Apague um contato e a entrada dele some na passagem seguinte.

## Calendário de feriados

O Radicale guarda assinatura, não só cópia. Na interface web, crie uma
coleção, escolha o tipo **Webcal** e cole o endereço em **Source**:

```
https://calendar.google.com/calendar/ical/pt.brazilian%23holiday%40group.v.calendar.google.com/public/basic.ics
```

Essa fonte traz de 2021 a 2031 em português, e é a data móvel que faz valer
assinar em vez de digitar: o Carnaval de 2026 sai como 13 a 18 de fevereiro,
da Sexta-feira às Cinzas, calculado a partir da Páscoa. Qualquer lista
estática erra isso dois anos depois.

Duas coisas a saber antes de depender disso:

**Quem baixa a fonte é o cliente, não o servidor.** O Radicale guarda e
anuncia a propriedade `source`; ele não faz requisição HTTP nenhuma. Apple
Calendar, Thunderbird e DAVx5 (pelo ICSx5) entendem calendário assinado e
buscam. Cliente que não entende mostra a coleção vazia.

**Só feriados nacionais.** Estaduais e municipais — muitas vezes os que de
fato mudam sua semana — não estão ali.

Nada a instalar: é recurso do próprio Radicale, sem script nem timer por trás.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale) — MIT

[Documentação oficial](https://radicale.org/v3.html)
