Open `http://<host-ip>:3000` or `https://homepage.<your-tailnet>.ts.net`.

### Widgets

None ship configured. To turn a card into a live reading — the queue, the free
space — add the labels to the service's own unit:

```ini
Label=homepage.widget.type=sonarr
Label=homepage.widget.url=http://sonarr:8989
Label=homepage.widget.key={{HOMEPAGE_VAR_SONARR_KEY}}
```

The URL is the container name: every service joins `tsdproxy-net`, so Homepage
reaches it without going out to the LAN.

`{{HOMEPAGE_VAR_X}}` is replaced by the environment variable of that name, read
from **this** service's `.env`. Use it for every key: it keeps the secret out
of a unit file, which in a public repository is the difference between a
password and a published password.

The [list of widgets](https://gethomepage.dev/widgets/) says what each type
needs. Most want an API key the app only issues after its first run.

### Update

`AutoUpdate=registry` is on: the image updates on its own.
