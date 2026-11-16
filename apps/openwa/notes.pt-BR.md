Abrir `http://<ip-do-host>:2785` ou `https://openwa.<your-tailnet>.ts.net`.

### Mudança de comportamento na 0.15.0

Enquanto o WhatsApp Web recarrega a própria página — medido em torno de cinco
minutos depois de um pareamento novo — todas as rotas do engine respondem `409`
em vez do `500` cru de antes. Cliente que tenta de novo em 5xx e desiste em 4xx
vai falhar onde antes se recuperava, então vale conferir os fluxos que chamam
essa API.
