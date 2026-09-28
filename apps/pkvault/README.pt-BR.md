# PKVault

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/pkvault.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Armazenamento de Pokémon e edição de saves no navegador, feito sobre o
[PKHeX](https://github.com/kwsch/PKHeX) — algo como o Pokémon HOME, para os seus
próprios arquivos de save. Mova Pokémon entre saves, guarde-os em bancos e caixas
fora de qualquer save, converta-os entre gerações e veja uma Pokédex única montada
a partir de todos os seus saves, da primeira geração ao Legends: Z-A.

## Instalação

```bash
qh pkvault            # mostra o plano
qh pkvault --apply
```

Depois abra `https://pkvault.<your-tailnet>.ts.net`.

**Não há login.** Quem alcançar a página pode editar e apagar seus saves. Na
tailnet, esse alguém é você. Com `--access tailnet`, o padrão, a porta da LAN
nem é publicada; com `local` ou `both`, a porta `8126` fica aberta a todo mundo
da sua rede — escolha esses só numa LAN que seja só sua.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixar a unit (não precisa clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/pkvault/pkvault.container

# 2. A pasta de dados: banco, armazenamento, backups, logs e saves enviados
mkdir -p ~/.config/containers/volumes/pkvault/data

systemctl --user daemon-reload
systemctl --user start pkvault
```

</details>

## Arquivos

```
pkvault.container   unit
install.ini         de onde vêm as atualizações
```

Tudo fica em `~/.config/containers/volumes/pkvault/data`: `db/` (SQLite),
`storage/` (os Pokémon guardados fora dos saves), `backup/`, `logs/`,
`saves-uploads/` e as configurações do app em `config/pkvault.json`.

## Colocando e tirando seus saves

O primeiro start cria um save de exemplo do Emerald, para o app ter o que
mostrar. Tire-o nas configurações quando os seus estiverem lá.

- **Enviar pelo navegador** — o jeito mais simples: até 5 arquivos, 60 MB no
  total, guardados em `saves-uploads/`. Cada save tem um botão de download para
  levar o arquivo editado de volta ao jogo ou emulador.
- **Uma pasta no host** — para saves que ficam nesta máquina. Ponha-os dentro do
  volume, por exemplo em `data/saves/`, e acrescente `/pkvault/saves/` aos locais
  de save nas configurações. **Copie com `cp`, não mova com `mv`**: medido, um
  arquivo movido de outra pasta mantém o rótulo SELinux antigo e o container não
  consegue lê-lo, enquanto a cópia recebe o rótulo da pasta.

Para manter os saves em sincronia com outros aparelhos, o projeto recomenda o
Syncthing (que este repositório também tem). Pasta montada por duas units usa
`:z`, não `:Z` — regra 16 das convenções.

Uma mudança só vai para o save quando você manda salvar no app, e antes de cada
gravação é feito um backup de todos os saves e do armazenamento. O
`BACKUP_FILE_COUNT_LIMIT=30` mantém os 30 mais recentes — sem ele a pasta só
cresce. Medido: com o limite em 2, quatro backups deixam dois no disco.

## Endurecimento

Raiz somente leitura, quatro capabilities (`chown`, `dac_override`, `setgid`,
`setuid`), sem `User=`. Testado exercitando o app — um save enviado, um backup
feito, um Pokémon movido de um save para o armazenamento e o save gravado de
volta.

A imagem roda o supervisord como root, com o nginx na 3000 na frente do backend
.NET na 5000. É isso que limita: o nginx, como root, escreve numa pasta do
usuário `nginx`, o que exige essas quatro capabilities, e o `supervisord.conf`
declara `user=root`, o que recusa qualquer outro usuário. Os detalhes estão
[nas recusas](../../docs/pt-BR/endurecimento.md#recusas-registradas).

Duas coisas na unit vêm daí:

- `Tmpfs=/var/lib/nginx/tmp` leva `mode=1777`: o nginx guarda ali todo envio
  acima de 16 KB, e sem isso enviar um save respondia 500.
- O `HealthCmd` pergunta à API, não só à página: com o nginx morto, o
  supervisord manteve o container `Up`, e `/api/settings` só responde quando o
  nginx e o backend respondem.

## Atualizar

```bash
qh pkvault --update --apply
```

Fixado em `2.3.3`. Nada atualiza sozinho. A imagem é marcada sem o `v` que a
release tem. O PKVault traz o próprio PKHeX (26.8.26 na 2.3.3), então o suporte a
um jogo novo chega com uma release do PKVault. A página consulta o GitHub em busca
de release nova a partir do seu navegador; é a única chamada para fora.

## Backup

```bash
qh pkvault --backup --apply --out ~/backups
```

Os backups do próprio app ficam no mesmo volume, então este copia eles também.

## Remover

```bash
qh pkvault --remove --apply           # para, mantém os dados
qh pkvault --remove --purge --apply   # e apaga o volume
```

O nó da tailnet não é removido por aqui — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status pkvault
podman logs -f pkvault
curl -s http://127.0.0.1:8126/api/settings   # versão, caminhos, PKHeX incluído
```

## Créditos

[Chnapy/PKVault](https://github.com/Chnapy/PKVault), de Richard Haddad — GPL-3.0.
Feito sobre o [PKHeX](https://github.com/kwsch/PKHeX), de Kaphotics — GPL-3.0.
Imagens e nomes de Pokémon são © The Pokémon Company.

[Documentação oficial](https://github.com/Chnapy/PKVault/blob/main/docs/functional/en/README.md)
