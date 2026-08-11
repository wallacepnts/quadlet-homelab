# SearXNG

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/searxng.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Metabuscador: manda a sua busca para dezenas de outros motores e junta os
resultados. Não guarda perfil, não põe cookie de rastreio, e quem vê a consulta
são os motores — vindo do servidor, não de você.

Ele também responde em JSON, que é o que o torna útil para o
[Open WebUI](../openwebui) — veja [abaixo](#open-webui).

## Instalação

```bash
qh searxng            # mostra o plano
qh searxng --apply
```

Abrir `https://searxng.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/searxng/config

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/searxng/searxng.container
wget -O ~/.config/containers/volumes/searxng/config/settings.yml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/searxng/config/settings.yml

# Assina o cookie de sessão
openssl rand -hex 32 | tr -d '\n' | podman secret create searxng-secret -

# O container roda como uid 977, que não é o seu depois do mapeamento
podman unshare chown -R 977:977 ~/.config/containers/volumes/searxng

systemctl --user daemon-reload
systemctl --user start searxng
```

</details>

## Arquivos

```
searxng.container      unit
config/settings.yml    as configurações, para dentro do volume
install.ini
```

O arquivo é curto por causa da primeira linha, `use_default_settings: true`: o
resto vem dos padrões de dentro da imagem, então a lista de motores de uma
versão nova chega sozinha, em vez de ficar congelada numa cópia aqui. O que
este repositório acrescenta é a saída em JSON.

O `secret_key` não está lá. A imagem geraria um no `settings.yml` no primeiro
start, mas esse arquivo vem daqui e é montado como somente-leitura, então a
chave entra como `${SEARXNG_SECRET}`, vinda de um secret do Podman — que os
padrões já leem.

## Open WebUI

O SearXNG responde `/search?q=...&format=json`, e é essa a interface que a
busca web do Open WebUI usa. Com ela, o modelo responde a partir de páginas
buscadas na hora da pergunta, e não só do que ele foi treinado.

No `~/.config/containers/env/openwebui.env`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Depois `qh openwebui --update --apply`. Os dois containers dividem a
`tsdproxy-net`, então `searxng` resolve pelo nome — sem IP do host e sem porta
publicada no meio.

O `format=json` não é padrão do SearXNG; sem o bloco `formats` no
`settings.yml` ele responde **403** para o que não é navegador, e a busca do
Open WebUI volta vazia em silêncio.

## Atualizar

```bash
qh searxng --update --apply
```

Fixado em `2026.8.10-0a118066d`. O SearXNG não publica release no GitHub e
marca por data mais commit, então o `qh-updates` compara com a lista de tags do
registry, e não com o redirect de release de sempre.

## Backup

```bash
qh searxng --backup --apply --out ~/backups
```

Há pouco a perder: o arquivo de configuração está neste repositório e o
histórico de busca não é de ninguém, nem do servidor. O backup existe pelas
preferências que você tenha ajustado.

Pra restaurar, por cima dos dados atuais:

```bash
qh searxng --restore ~/backups/searxng-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh searxng --remove --apply           # para e tira, mantendo o volume
qh searxng --remove --purge --apply   # e apaga o volume e o secret
```

## Comandos

```bash
systemctl --user status searxng
podman logs -f searxng

# o que o Open WebUI enxerga
podman exec searxng wget -qO- 'http://127.0.0.1:8080/search?q=podman&format=json' | head -c 200
```

## Créditos

[searxng/searxng](https://github.com/searxng/searxng) — AGPL-3.0.

[Documentação oficial](https://docs.searxng.org/)
