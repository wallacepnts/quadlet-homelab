The install ends by printing the **registration token**. Enter it in the FMD app when you point it at `https://fmd.<your-tailnet>.ts.net`.

**It must be served over HTTPS**: the web interface does not work over plain HTTP, so LAN-only access (port `8124`) leaves it unusable. The **phone** reports to the tailnet address, which resolves only while Tailscale runs on it: keep Tailscale always-on there, or a lost phone reports nothing.
