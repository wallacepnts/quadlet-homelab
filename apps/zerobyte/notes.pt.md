O Zerobyte chama um **hook de backup** antes e depois de cada tarefa, para o Restic nunca copiar um banco no meio de uma escrita. Por unit há dois modos: `sqlite` (cópia online para `<volume>/.dbbackup/`, sem parada) e `stop` (para a unit durante a cópia, o padrão). O hook roda no host, porque parar uma unit é `systemctl --user`.

```bash
# em quais units ele pode agir, e como (o que não está na lista recebe 404)
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=vaultwarden:sqlite,any-sync-bundle:stop

mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8766/healthz     # {"ok": true}
```

Cada tarefa leva então `http://<host-ip>:8766/hooks/<unit>/pre-backup` e `.../post-backup`, que o `qh --zerobyte` escreve para você e confere com a lista: uma unit que falta ali é um backup que falha às 03:00 com um 404 que ninguém vê. `ZEROBYTE_HOOK_PORT` muda a porta (`WEBHOOK_ALLOWED_ORIGINS` precisa concordar).
