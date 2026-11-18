A instalação termina imprimindo o usuário e a senha. Em cada cliente, aponte a sincronização para `https://anki.<your-tailnet>.ts.net/` e entre com eles:

- **Anki (desktop)**: Preferências → Sincronização → *Servidor de sincronização próprio*.
- **AnkiDroid**: Configurações → Sincronização → *Servidor de sincronização personalizado*.
- **AnkiMobile**: Configurações → Sincronização → *Servidor personalizado*.

A primeira sincronização depois da troca é completa: envie do dispositivo que tem a coleção que você quer manter e baixe nos outros.

**Não há página web**: o endereço mostra `404 Not Found` e isso é o servidor funcionando. Use o endereço HTTPS da tailnet (o AnkiMobile recusa servidor sem TLS); o celular precisa estar com o Tailscale ligado.

Para escolher a senha: `qh anki --reinstall --ask-secrets --apply` e digite **`anki:sua-senha`**, usuário e senha juntos. Mantenha o usuário `anki`: as coleções ficam numa pasta com esse nome.
