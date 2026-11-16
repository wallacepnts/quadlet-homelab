# Memos

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Self-hosted quick notes, markdown-native and lightweight.

## First run

Open `http://<host-ip>:5230` or `https://memos.<your-tailnet>.ts.net` and
create the account. **The first user to sign up becomes admin**, with no email
confirmation. Right after that, turn signup off in Settings → "Allow user
signup", or anyone who reaches the URL can create an account.

## Files

```
memos.container   unit
.env.example      environment
```

Data in `~/.config/containers/volumes/memos/data` on port **5230**.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[Memos](https://github.com/usememos/memos) — MIT

[Official documentation](https://www.usememos.com/docs)
