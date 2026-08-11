# Vikunja

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/vikunja.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Tarefas que pertencem a um projeto e têm data: a mesma lista mostrada como
lista, quadro kanban, tabela ou gráfico de gantt, com subtarefa, etiqueta,
anexo e lembrete.

Ao lado do [donetick](../donetick/README.pt-BR.md), a divisão é o propósito. O
donetick é para a tarefa que volta — lixo na terça, filtro a cada seis meses.
Este é para o trabalho que acaba: uma mudança, uma reforma, uma viagem.

## Instalação

```bash
qh vikunja            # mostra o plano
qh vikunja --apply
```

Abrir `https://vikunja.<your-tailnet>.ts.net` e se cadastrar. Depois ponha
`VIKUNJA_SERVICE_ENABLEREGISTRATION=false` no `.env` e reinicie, senão quem
alcança a sua tailnet cria conta.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/vikunja/{db,files}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vikunja/vikunja.container
wget -O ~/.config/containers/env/vikunja.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vikunja/.env.example
# editar ~/.config/containers/env/vikunja.env: VIKUNJA_SERVICE_PUBLICURL

# O container roda como uid 1000, que não é o seu depois do mapeamento
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/vikunja

systemctl --user daemon-reload
systemctl --user start vikunja
```

</details>

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

```bash
qh vikunja --update --apply
```

Fixado em `2.5.0`. Ele migra o banco no start, e é por isso que as notas da
release valem uma lida antes de uma major.

## Backup

```bash
qh vikunja --backup --apply --out ~/backups
```

Para o serviço, empacota os dois volumes e o `.env`, e sobe de novo.

Pra restaurar, por cima dos dados atuais:

```bash
qh vikunja --restore ~/backups/vikunja-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh vikunja --remove --apply           # para e mantém as tarefas
qh vikunja --remove --purge --apply   # e apaga elas
```

## Comandos

```bash
systemctl --user status vikunja
podman logs -f vikunja

# um usuário, sem a interface
podman exec vikunja /app/vikunja/vikunja user list
```

## Créditos

[go-vikunja/vikunja](https://github.com/go-vikunja/vikunja) — AGPL-3.0.

[Documentação oficial](https://vikunja.io/docs/)
