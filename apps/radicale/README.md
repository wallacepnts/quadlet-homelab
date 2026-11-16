# Radicale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A light, minimal CalDAV/CardDAV server.

## First run

Open `http://<host-ip>:5232` or `https://radicale.<your-tailnet>.ts.net`.

## Files

```
radicale.container   unit
.env.example         environment
config/config        Radicale's own config, into the volume
birthday-sync/       the timer and its service, into systemd/user
install.ini
```

## Birthday calendar

A timer reads the birthdays out of your contacts and keeps a calendar named
`birthdays` in sync with them, so a new contact shows up as a yearly event
without you entering it twice.

The script that does it comes inside the image — this is a rebuild of
`tomsquest/docker-radicale` carrying it, because the script imports `vobject`
and `dateutil` and the official image has neither. Installing them at run time
is not possible either: this container is `ReadOnly=true`.

The install puts the timer in place; enabling it is one command, once:

```bash
systemctl --user enable --now radicale-birthday-sync.timer
```

It runs 5 minutes after boot and every 30 minutes after that. Check it with:

```bash
systemctl --user list-timers radicale-birthday-sync.timer
journalctl --user -u radicale-birthday-sync.service -n 20
```

The `birthdays` calendar is created on the first run, in each user's own
collection. Delete a contact and its entry goes away on the next pass.

## Holiday calendar

Radicale can hold a subscription instead of a copy. In the web interface,
create a collection, pick **Webcal** as the type and paste the feed in
**Source**:

```
https://calendar.google.com/calendar/ical/pt.brazilian%23holiday%40group.v.calendar.google.com/public/basic.ics
```

That feed carries 2021 to 2031 in Portuguese, and it is the moving dates that
make it worth subscribing to rather than typing: Carnaval 2026 comes out as 13
to 18 February, Sexta-feira through the Cinzas, computed from Easter. Any
static list gets that wrong two years later.

Two things to know before relying on it:

**The client downloads the feed, not the server.** Radicale stores and
advertises the `source` property; it makes no HTTP request of its own. Apple
Calendar, Thunderbird and DAVx5 (through ICSx5) understand subscribed
calendars and fetch it. A client that does not will show the collection empty.

**National holidays only.** State and municipal ones — often the days that
actually change your week in Brazil — are not in it.

Nothing to install: this is upstream Radicale's own feature, and there is no
script or timer behind it.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale) — MIT

[Official documentation](https://radicale.org/v3.html)
