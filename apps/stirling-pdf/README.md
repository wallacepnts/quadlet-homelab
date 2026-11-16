# Stirling-PDF

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Local PDF manipulation — merge, split, convert, OCR and sign, in place of the "online PDF" sites.

## First run

Open `http://<host-ip>:8095` or `https://stirling-pdf.<your-tailnet>.ts.net`.

## Files

```
stirling-pdf.container
.env.example
install.ini
```

## What 3.0 changed

**Analytics.** Left unset, 3.0 asks the admin on first login whether to send
usage data (PostHog and Scarf). The `.env` ships `SYSTEM_ENABLEANALYTICS=false`,
so it never asks and never sends. An install from before 3.0 keeps its old
`.env` on `--update` — add that line to `~/.config/containers/env/stirling-pdf.env`
by hand.

**A usage allowance.** The new batch "Processor", the API and the AI features
are free up to 1,000 PDFs a month. The editor itself — opening a PDF and using
a tool on it — stays free and unlimited, which is what this service is here for.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) — MIT

[Official documentation](https://stirling.com)
