Open `http://<host-ip>:8095` or `https://stirling-pdf.<your-tailnet>.ts.net`.

### What 3.0 changed

**Analytics.** Left unset, 3.0 asks the admin on first login whether to send
usage data (PostHog and Scarf). The `.env` ships `SYSTEM_ENABLEANALYTICS=false`,
so it never asks and never sends. An install from before 3.0 keeps its old
`.env` on `--update` — add that line to `~/.config/containers/env/stirling-pdf.env`
by hand.

**A usage allowance.** The new batch "Processor", the API and the AI features
are free up to 1,000 PDFs a month. The editor itself — opening a PDF and using
a tool on it — stays free and unlimited, which is what this service is here for.
