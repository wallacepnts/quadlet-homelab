# FileBrowser Quantum

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/filebrowser-quantum.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gerenciador de arquivos web: navegar, buscar, pré-visualizar, subir, baixar,
compartilhar por link e editar texto, sobre um diretório que você escolhe.

## Primeiro acesso

Coloque seus arquivos em `~/.config/containers/volumes/filebrowser/files/` e
abra `https://filebrowser.<your-tailnet>.ts.net` ou `http://<ip-do-host>:8014`.

O usuário é `admin`. A senha sai no fim da instalação, e de novo com
`qh filebrowser`.

## Arquivos

```
filebrowser.container   unit
config.yaml.example     config do app — sem ele o app não sobe
.env.example            ambiente
install.ini             receitas de secret, login, nome no upstream
```

## Volumes

| caminho | guarda |
| --- | --- |
| `volumes/filebrowser/data` | `config.yaml`, `database.db`, cache de miniaturas |
| `volumes/filebrowser/files` | os arquivos que ele gerencia |

A porta **8014** do host mapeia pra **8080** lá dentro.

## Acrescentar um diretório

Um `Volume=` na unit e a fonte correspondente no `config.yaml`:

```ini
Volume=%h/Documentos:/docs:Z
```

```yaml
server:
  sources:
    - path: "/srv"
    - path: "/docs"
```

Cada fonte ganha o próprio índice. Árvore grande custa memória e uma varredura
na primeira execução.

## Senha

```bash
qh filebrowser        # imprime usuário e senha
```

Pra trocar:

```bash
podman secret rm filebrowser-admin-password
podman secret create filebrowser-admin-password -   # digite, Enter, Ctrl-D
systemctl --user restart filebrowser
```

Rotacionar o `filebrowser-jwt-secret` do mesmo jeito derruba todas as sessões
sem mudar a senha.

## Atualizar

O `config.yaml` é versionado aqui, então leia as notas da release atrás de mudança de schema antes de subir uma major.

## Backup

Parado de propósito: o `database.db` é um banco vivo, e copiar com o app
escrevendo dá um arquivo que só falha na hora de restaurar.

Só os metadados, sem os arquivos:

## Créditos

[gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser) — Apache-2.0

[Documentação oficial](https://filebrowserquantum.com/en/docs/)
