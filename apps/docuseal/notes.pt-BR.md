Abrir `https://docuseal.<your-tailnet>.ts.net` e criar a primeira conta — é
essa a configuração. Depois ponha o seu endereço no `HOST` do `.env` e
reinicie, senão os links que você mandar apontam para o hostname do container.

### SQLite, não PostgreSQL

O padrão do próprio DocuSeal é SQLite, e é o que esta unit usa. O compose
oficial mostra PostgreSQL num segundo container — certo para uma empresa, um
container e mais um banco para fazer backup numa casa. Regra deste repositório:
SQLite sempre que o projeto oferecer.

### O mount desce um nível

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

### O HOST é o que a outra parte clica

O `HOST` do `.env` é a base dos links de assinatura. Errado, e a pessoa para
quem você mandou o documento recebe um link que não abre — a falha cai no colo
dela, não no seu, que é o pior lugar possível.

### Backup

Para o serviço, empacota o banco e os documentos, e sobe de novo. Documento
assinado que você não consegue apresentar depois é documento que você não
assinou, então vale conferir este backup depois do primeiro uso real.
