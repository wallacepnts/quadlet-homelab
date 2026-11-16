# DocuSeal

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/docuseal.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Assinatura de documentos, em casa. Você sobe um PDF, marca onde vão assinatura,
rubrica e data, manda um link, e a outra parte assina no navegador — com o
arquivo e a trilha de auditoria ficando no seu disco.

Substitui entregar um contrato a uma empresa para que ele seja assinado, que é
a parte dessa transação em que ninguém pensa: o documento, as partes e os
carimbos de tempo acabam todos no banco de dados de outra pessoa.

## Primeiro acesso

Abrir `https://docuseal.<your-tailnet>.ts.net` e criar a primeira conta — é
essa a configuração. Depois ponha o seu endereço no `HOST` do `.env` e
reinicie, senão os links que você mandar apontam para o hostname do container.

## Arquivos

```
docuseal.container   unit
.env.example         ambiente
```

O volume guarda o `db.sqlite3` e os documentos enviados. É tudo: os modelos, as
assinaturas e a trilha de auditoria que dá valor a uma assinatura.

## SQLite, não PostgreSQL

O padrão do próprio DocuSeal é SQLite, e é o que esta unit usa. O compose
oficial mostra PostgreSQL num segundo container — certo para uma empresa, um
container e mais um banco para fazer backup numa casa. Regra deste repositório:
SQLite sempre que o projeto oferecer.

## O mount desce um nível

```ini
Volume=%h/.config/containers/volumes/docuseal/data:/data/docuseal:Z
```

Não em `/data`. O app cria o `/data/docuseal/` sozinho no primeiro start, e
como usuário não-root num sistema de arquivos somente-leitura ele não consegue:

```
Permission denied @ rb_sysopen - /data/docuseal/docuseal.env
```

Montar direto no caminho que ele quer elimina o passo de criação. Medi das duas
formas antes de decidir.

## O HOST é o que a outra parte clica

O `HOST` do `.env` é a base dos links de assinatura. Errado, e a pessoa para
quem você mandou o documento recebe um link que não abre — a falha cai no colo
dela, não no seu, que é o pior lugar possível.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1000`. Medido com a aplicação servindo — Puma escutando e a interface
respondendo —, não só com o container de pé.

## Backup

Para o serviço, empacota o banco e os documentos, e sobe de novo. Documento
assinado que você não consegue apresentar depois é documento que você não
assinou, então vale conferir este backup depois do primeiro uso real.

## Créditos

[docusealco/docuseal](https://github.com/docusealco/docuseal) — AGPL-3.0.

[Documentação oficial](https://www.docuseal.com/docs)
