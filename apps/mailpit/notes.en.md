The install prints the user and password at the end. Open `http://<host-ip>:8025` or `https://mailpit.<your-tailnet>.ts.net`.

Point your app at the SMTP port: host `<host-ip>`, port **1025**, no authentication, no TLS. The web UI asks for the password; the SMTP port does not, on purpose.
