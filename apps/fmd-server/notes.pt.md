A instalação termina imprimindo o **token de registro**. Informe-o no app FMD ao apontá-lo para `https://fmd.<your-tailnet>.ts.net`.

**Ele precisa ser servido por HTTPS**: a interface web não funciona em HTTP puro, então o acesso só pela rede local (porta `8124`) a deixa inutilizável. O **celular** reporta para o endereço da tailnet, que só resolve com o Tailscale rodando nele: deixe o Tailscale sempre ligado lá, ou um celular perdido não reporta nada.
