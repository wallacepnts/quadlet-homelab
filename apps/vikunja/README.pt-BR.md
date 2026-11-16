# Vikunja

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/vikunja.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Tarefas que pertencem a um projeto e têm data: a mesma lista mostrada como
lista, quadro kanban, tabela ou gráfico de gantt, com subtarefa, etiqueta,
anexo e lembrete.

Ao lado do [donetick](../donetick/README.pt-BR.md), a divisão é o propósito. O
donetick é para a tarefa que volta — lixo na terça, filtro a cada seis meses.
Este é para o trabalho que acaba: uma mudança, uma reforma, uma viagem.

## Primeiro acesso

Abrir `https://vikunja.<your-tailnet>.ts.net` e se cadastrar. Depois ponha
`VIKUNJA_SERVICE_ENABLEREGISTRATION=false` no `.env` e reinicie, senão quem
alcança a sua tailnet cria conta.

## Arquivos

```
vikunja.container   unit
.env.example        ambiente
```

Dois volumes de propósito: `db/` para o `vikunja.db` e `files/` para os anexos.
Separados, um backup distingue banco corrompido de arquivo faltando, e
restaurar um não passa por cima do outro.

## O PUBLICURL não é enfeite

O `VIKUNJA_SERVICE_PUBLICURL` é o endereço em que o frontend chama a API.
Errado, e o sintoma engana: a interface carrega, parece certa, e toda
requisição falha. É também o que os links de convite e de lembrete carregam.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1000` — o uid que a própria imagem declara. Medido com as migrações
rodadas e a API respondendo, não só com o container de pé.

O healthcheck é o subcomando do próprio binário, em forma exec:

```ini
HealthCmd=["CMD", "/app/vikunja/vikunja", "healthcheck"]
```

A imagem é distroless — `/app/vikunja/vikunja` e um pacote de certificados são
tudo o que há dentro —, então o `CMD-SHELL` não teria shell onde rodar.

## Atualizar

Ele migra o banco no start, e é por isso que as notas da release valem uma lida antes de uma major.

## Backup

Para o serviço, empacota os dois volumes e o `.env`, e sobe de novo.

## Créditos

[go-vikunja/vikunja](https://github.com/go-vikunja/vikunja) — AGPL-3.0.

[Documentação oficial](https://vikunja.io/docs/)
