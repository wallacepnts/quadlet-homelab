O primeiro start leva um ou dois minutos: o server cria o schema do banco (uns
30 s medidos) e só então a interface web sobe. Depois abra
`https://zabbix.<your-tailnet>.ts.net`.

**O primeiro login é o padrão do próprio Zabbix, `Admin` / `zabbix`.** A imagem
não tem configuração para isso, então a instalação não consegue gerar uma senha.
Troque na hora: *Users → Users → Admin → Change password*.

### PostgreSQL, não SQLite

O repositório prefere SQLite, mas o server do Zabbix não tem modo SQLite: roda em
PostgreSQL ou MySQL, e SQLite existe só para o *proxy*. O PostgreSQL é o que o
compose do próprio projeto usa, e a major (17) é a que ele valida.

### O host "Zabbix server" nasce com o agente quebrado

Uma instalação nova traz um host chamado *Zabbix server* cujo agente é esperado
em `127.0.0.1:10050`. Não há agente nesta stack, então os itens falham com
"network error" e o host fica vermelho. Desative esse host, ou instale um agente
em algum lugar e aponte o host para ele.

Para monitorar uma máquina, instale o agente do Zabbix nela e faça-o alcançar
este host na porta **10051** (checagens ativas), ou deixe o server alcançar o
agente na **10050** (passivas). As duas são TCP simples, na tailnet ou na LAN.

### Atualização

O server e a interface web compartilham uma tag e têm de andar juntos. O server atualiza o próprio schema ao subir, então faça um backup antes de um salto de minor. O Postgres fica na 17.

### Backup

A frio, como as outras stacks com banco: para as três units, empacota o volume e
o segredo, e sobe de novo.

### Remover

O nó da tailnet não é desregistrado por isso — é feito no admin do Tailscale.
