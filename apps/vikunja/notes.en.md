Open `https://vikunja.<your-tailnet>.ts.net` and register. Then set `VIKUNJA_SERVICE_ENABLEREGISTRATION=false` in the `.env` and restart, or anyone who reaches your tailnet can create an account.

`VIKUNJA_SERVICE_PUBLICURL` must be the address you open it at: wrong, the page loads and every request fails.
