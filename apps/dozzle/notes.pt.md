Abra `https://dozzle.<your-tailnet>.ts.net`.

O socket do Podman é montado só para leitura: isso impede de criar ou matar qualquer coisa, mas ele ainda **lê os logs e o ambiente de todo container**, segredos inclusos, e quem abre a página lê tudo. Duas opções no `.env` reduzem isso: `DOZZLE_AUTH_PROVIDER=simple` põe um login na frente (desligado por padrão, só serve numa tailnet em que você está sozinho) e `DOZZLE_FILTER=name=jellyfin` limita aos containers que você nomear.
