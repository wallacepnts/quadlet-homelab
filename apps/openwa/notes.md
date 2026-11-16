Open `http://<host-ip>:2785` or `https://openwa.<your-tailnet>.ts.net`.

### Behaviour change in 0.15.0

While WhatsApp Web reloads its own page — measured around five minutes after a
fresh pairing — every engine route answers `409` instead of the raw `500` it
used to. A client that retries on 5xx and gives up on 4xx will now fail where
it used to recover, so check the flows that call this API.
