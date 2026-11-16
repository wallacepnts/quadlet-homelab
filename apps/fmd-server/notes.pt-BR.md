A instalação termina imprimindo o **token de registro**. Digite-o no app FMD
quando apontá-lo para `https://fmd.<your-tailnet>.ts.net`.

### Como se chega nele — e como o celular chega nele

**O FMD Server precisa ser servido por HTTPS**: a interface web não funciona em
HTTP puro. Na tailnet, o tsdproxy resolve isso. A porta `8124` na LAN é HTTP
puro, então escolher acesso só pela LAN na instalação deixa a interface web
inutilizável.

A parte fácil de esquecer: o **celular** reporta para
`fmd.<your-tailnet>.ts.net`, que só resolve com o app do Tailscale rodando no
celular. Deixe o Tailscale sempre ligado lá — um celular perdido com o Tailscale
desligado não reporta nada, por melhor que este lado esteja. O app FMD também
aceita comandos por SMS, que não dependem deste servidor.

### O token de registro

O FMD Server só confere o token quando há um definido, e esta unit sempre
define. Medido na 0.17.0: com `FMD_REGISTRATIONTOKEN` ausente, um registro com
token errado é aceito; com ele definido, o mesmo pedido responde
`401 Registration Token not valid`. O token só importa para **criar** contas —
uma conta existente entra com a própria senha.

### Atualizar

O projeto é **pré-1.0, e avisa que versões minor podem quebrar** — leia as notas
da release antes de ir da 0.17 para a 0.18, e faça backup antes. Ele vive no
GitLab, então o `install.ini` compara com o registry de lá em vez de uma
página de releases do GitHub.

A variante `-alpine`, e não a Debian padrão nem a distroless menor, porque é a
que traz `wget` — de que o `HealthCmd` precisa, e o `Notify=healthy` precisa
do `HealthCmd` (regra 14 das convenções).

### Backup

O volume guarda um banco SQLite. É texto cifrado, então o backup só serve junto
com as senhas das contas.
