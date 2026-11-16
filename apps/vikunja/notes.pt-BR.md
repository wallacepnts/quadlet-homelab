Abrir `https://vikunja.<your-tailnet>.ts.net` e se cadastrar. Depois ponha
`VIKUNJA_SERVICE_ENABLEREGISTRATION=false` no `.env` e reinicie, senão quem
alcança a sua tailnet cria conta.

### O PUBLICURL não é enfeite

O `VIKUNJA_SERVICE_PUBLICURL` é o endereço em que o frontend chama a API.
Errado, e o sintoma engana: a interface carrega, parece certa, e toda
requisição falha. É também o que os links de convite e de lembrete carregam.

### Atualizar

Ele migra o banco no start, e é por isso que as notas da release valem uma lida antes de uma major.

### Backup

Para o serviço, empacota os dois volumes e o `.env`, e sobe de novo.
