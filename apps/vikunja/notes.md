Open `https://vikunja.<your-tailnet>.ts.net` and register. Then set
`VIKUNJA_SERVICE_ENABLEREGISTRATION=false` in the `.env` and restart, or anyone
who reaches your tailnet can create an account.

### PUBLICURL is not decoration

`VIKUNJA_SERVICE_PUBLICURL` is the address the frontend calls the API on.
Wrong, and the symptom misleads: the interface loads, looks right, and every
request fails. It is also what invitation and reminder links carry.

### Update

It migrates the database on start, which is why the release notes are worth a look before a major bump.

### Backup

Stops it, packs both volumes and the `.env`, starts it again.
