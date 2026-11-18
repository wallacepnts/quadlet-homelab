Open `https://postiz.<your-tailnet>.ts.net` and create your account. The first sign-up works and then the page closes (`DISABLE_REGISTRATION=true` is in the `.env`). To add someone later, set it to `false`, restart, create the account, and set it back.

The address has to be the tailnet one: Postiz builds its sign-in and OAuth links from it, and Meta only accepts an HTTPS redirect.

The `nginx.conf` this folder installs rewrites the session cookie's `Domain` (`proxy_cookie_domain .ts.net $host;`): `ts.net` is a public suffix, so browsers refuse a cookie for it and the login loops. It is the project's `var/docker/nginx.conf` plus those two lines: **on a version bump, compare them** and carry the lines over.
