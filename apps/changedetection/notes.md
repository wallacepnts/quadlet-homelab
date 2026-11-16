Open `https://changedetection.<your-tailnet>.ts.net`. Set a password under
**Settings → General** if anyone else reaches your tailnet.

### Notifications

It speaks [Apprise](https://github.com/caronc/apprise), so the destination is a
URL. For the [ntfy](../ntfy) in this repository, under **Settings →
Notifications**:

```
ntfy://ntfy:2586/changes
```

`BASE_URL` in the `.env` is what the links inside those messages point at.
Without it they carry the container's hostname, which resolves nowhere on your
phone.

### Pages that need a browser

The default fetch is a plain HTTP request: fast, cheap, and enough for most
pages. A page that renders its content with JavaScript comes back empty, and
the visual element picker needs a real browser too.

The answer is a Chrome sidecar and the commented `PLAYWRIGHT_DRIVER_URL` line
in the `.env`. It is left off here on purpose — it is a second container with a
browser inside, which is a lot of machinery for a page you can usually watch
through its JSON endpoint instead. Look for one before adding half a gigabyte
of Chrome.

### Backup

Stops it, packs the datastore and the `.env`, starts it again.
