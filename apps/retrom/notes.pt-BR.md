Coloque os jogos em `~/.config/containers/volumes/retrom/library`, na
[estrutura de pastas que o Retrom
espera](https://github.com/JMBeresford/retrom/wiki/Library-Structure), e abra
`http://<ip-do-host>:5101` ou `https://retrom.<your-tailnet>.ts.net`.

**O primeiro start leva uns 90 segundos** — ele baixa o EmulatorJS e roda as
migrações do banco. O `TimeoutStartSec=300` e os 180 segundos de carência do
healthcheck existem por isso; os restarts seguintes são rápidos.

### Metadados

Capas e descrições vêm do IGDB ou do SteamGridDB, e os dois pedem chave de
API. Sem chave a biblioteca funciona igual, listada pelo nome do arquivo. As
chaves são configuradas pelo cliente, não aqui — veja [Metadata
Providers](https://github.com/JMBeresford/retrom/wiki/Metadata-Providers).

### Backup

Para o serviço, empacota os três volumes e o `.env`, e religa. A frio de
propósito: o Retrom carrega um PostgreSQL embutido, e copiá-lo em uso dá um
arquivo que só falha na hora de restaurar. É também por isso que o modo a usar
no [gancho de backup do Zerobyte](../zerobyte) é o `stop`.

### Remover

O `--purge` apaga a biblioteca junto — os jogos ficam num volume como todo o
resto.
