O primeiro início leva um ou dois minutos (ele cria o esquema do banco). Depois abra `https://zabbix.<your-tailnet>.ts.net`.

**O primeiro login é o padrão do próprio Zabbix, `Admin` / `zabbix`.** A imagem não tem opção para isso, então troque a senha logo: *Usuários → Usuários → Admin → Alterar senha*.

O host "Zabbix server" começa vermelho: o agente dele é esperado em `127.0.0.1:10050` e esta pilha não tem agente. Desative esse host. Para monitorar uma máquina, instale o agente do Zabbix nela e faça-o alcançar este host na porta **10051** (ativo), ou deixe o servidor alcançá-lo na **10050** (passivo).
