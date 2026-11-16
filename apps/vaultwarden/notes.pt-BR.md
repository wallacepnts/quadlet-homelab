Abrir `https://vaultwarden.<your-tailnet>.ts.net`.

O cofre é alcançável só pela tailnet. O `PublishPort=8082:80` vem comentado na
unit: publicar a porta faria ele atender também a qualquer um na LAN, que é
porta mais larga do que um cofre de senhas precisa. Descomente se quiser o
`http://<ip-do-host>:8082` também.
