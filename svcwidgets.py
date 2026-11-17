#!/usr/bin/env python3
"""Service widgets: a few numbers from inside an app, shown on its tile (Homepage calls them service widgets).

An app says which in its `app.json` (`"widgets": [{"type": "immich"}]`, or `{"type": "sonarr", "unit":
"media-stack-sonarr"}` in a folder of several). The credential each one needs (an API key, a user and a
password, a status page's slug) is typed in the panel and kept on the server in
`~/.config/quadlet-homelab/widgets.json` (mode 600). The store calls the app's API **from the server**, so the
key never reaches the browser, and the browser only ever sees the numbers.

Each type is a function of (address, credential, get) that returns its fields: [{key, value, kind, level}],
`kind` being "count", "bytes", "ms" or "pct" for the page to format, and `level` "good", "warn" or "bad" where
the number calls for attention (Homepage's `highlight`).

    python3 svcwidgets.py --selftest
"""

import base64
import json
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

AUTH = {"key": ("key",), "userpass": ("user", "password"), "slug": ("slug",)}
FIELD_LABELS = {
    "photos": ("photos", "fotos"), "videos": ("videos", "vídeos"), "storage": ("storage", "armazenamento"),
    "queries": ("queries", "consultas"), "blocked": ("blocked", "bloqueadas"), "blocked_pct": ("blocked", "bloqueado"),
    "latency": ("latency", "latência"), "documents": ("documents", "documentos"), "inbox": ("inbox", "na caixa de entrada"),
    "up": ("up", "no ar"), "down": ("down", "fora do ar"), "wanted": ("wanted", "faltando"), "queued": ("queued", "na fila"),
    "series": ("series", "séries"), "movies": ("movies", "filmes"), "streams": ("playing", "tocando agora"),
    "songs": ("songs", "músicas"),
}


def http_get(url, headers=None, timeout=8):
    """JSON from an app's API. The certificate is not checked: the address is one of our own units
    (the tailnet name tsdproxy serves, or a LAN port), and a self-signed app is still the app."""
    req = urllib.request.Request(url, headers={"User-Agent": "qh-store", "Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context()) as r:
        return json.loads(r.read(4 << 20))


def f(key, value, kind="count", level=None):
    return {"key": key, "value": value, "kind": kind, "level": level}


def immich(url, c, get):
    d = get(f"{url}/api/server/statistics", {"x-api-key": c["key"]})
    return [f("photos", d.get("photos")), f("videos", d.get("videos")), f("storage", d.get("usage"), "bytes")]


def adguard(url, c, get):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    d = get(f"{url}/control/stats", {"Authorization": f"Basic {tok}"})
    q, b = d.get("num_dns_queries") or 0, d.get("num_blocked_filtering") or 0
    return [f("queries", q), f("blocked", b), f("blocked_pct", round(100 * b / q, 1) if q else 0, "pct"),
            f("latency", round((d.get("avg_processing_time") or 0) * 1000, 1), "ms")]


def paperless(url, c, get):
    d = get(f"{url}/api/statistics/", {"Authorization": f"Token {c['key']}"})
    inbox = d.get("documents_inbox") or 0
    return [f("documents", d.get("documents_total")), f("inbox", inbox, level="warn" if inbox else None)]


def uptime_kuma(url, c, get):
    d = get(f"{url}/api/status-page/heartbeat/{urllib.parse.quote(c['slug'], safe='')}")
    ultimos = [beats[-1].get("status") for beats in (d.get("heartbeatList") or {}).values() if beats]
    fora = sum(1 for s in ultimos if s == 0)
    return [f("up", sum(1 for s in ultimos if s == 1), level="good"), f("down", fora, level="bad" if fora else None)]


def _arr(url, c, get, contar):
    h = {"X-Api-Key": c["key"]}
    fila = get(f"{url}/api/v3/queue?pageSize=1", h).get("totalRecords", 0)
    falta = get(f"{url}/api/v3/wanted/missing?pageSize=1", h).get("totalRecords", 0)
    return [f("wanted", falta, level="warn" if falta else None), f("queued", fila), f(contar, len(get(f"{url}/api/v3/{contar[:-1] if contar == 'movies' else contar}", h)))]


def sonarr(url, c, get):
    return _arr(url, c, get, "series")


def radarr(url, c, get):
    return _arr(url, c, get, "movies")


def jellyfin(url, c, get):
    h = {"X-Emby-Token": c["key"]}
    tocando = sum(1 for s in get(f"{url}/Sessions", h) if s.get("NowPlayingItem"))
    n = get(f"{url}/Items/Counts", h)
    return [f("streams", tocando), f("movies", n.get("MovieCount")), f("series", n.get("SeriesCount")), f("songs", n.get("SongCount"))]


TYPES = {"immich": ("key", immich), "adguard": ("userpass", adguard), "paperless": ("key", paperless),
         "uptime-kuma": ("slug", uptime_kuma), "sonarr": ("key", sonarr), "radarr": ("key", radarr),
         "jellyfin": ("key", jellyfin)}


def config_file(home):
    return Path(home) / ".config/quadlet-homelab/widgets.json"


def load(home):
    try:
        d = json.loads(config_file(home).read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(home, d):
    p = config_file(home)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2) + "\n")
    p.chmod(0o600)


def slot(app, w):
    """The key a widget's credential is stored under: the app, and the unit when the folder has several."""
    return f"{app}/{w['unit']}" if w.get("unit") else app


def configured(tipo, cred):
    return all(str((cred or {}).get(k, "")).strip() for k in AUTH[TYPES[tipo][0]])


def read(tipo, url, cred, get=http_get):
    """{fields} or {error}: what one widget says now. A wrong key is an error on the card, never a crash."""
    try:
        return {"fields": TYPES[tipo][1](url.rstrip("/"), cred, lambda u, h=None: get(u, h))}
    except Exception as e:                                    # the app's API, its network, its JSON: all theirs
        codigo = getattr(e, "code", None)
        return {"error": f"HTTP {codigo}" if codigo else type(e).__name__}


def selftest():
    respostas = {
        "/api/server/statistics": {"photos": 1200, "videos": 30, "usage": 5 * 2 ** 30},
        "/control/stats": {"num_dns_queries": 1000, "num_blocked_filtering": 125, "avg_processing_time": 0.0123},
        "/api/statistics/": {"documents_total": 812, "documents_inbox": 3},
        "/api/status-page/heartbeat/home": {"heartbeatList": {"1": [{"status": 0}, {"status": 1}], "2": [{"status": 0}], "3": []}},
        "/api/v3/queue?pageSize=1": {"totalRecords": 2}, "/api/v3/wanted/missing?pageSize=1": {"totalRecords": 7},
        "/api/v3/series": [{}, {}, {}], "/api/v3/movie": [{}],
        "/Sessions": [{"NowPlayingItem": {"Name": "x"}}, {}], "/Items/Counts": {"MovieCount": 40, "SeriesCount": 9, "SongCount": 900},
    }
    vistos = []
    def get(u, h=None):
        vistos.append((u, h or {}))
        return respostas[u.split("://x", 1)[1]]
    val = lambda r: {x["key"]: (x["value"], x["level"]) for x in r["fields"]}
    assert val(read("immich", "http://x/", {"key": "k"}, get)) == {"photos": (1200, None), "videos": (30, None), "storage": (5 * 2 ** 30, None)}
    assert vistos[-1][1] == {"x-api-key": "k"}, "the key goes in the header the app expects"
    a = val(read("adguard", "http://x", {"user": "u", "password": "p"}, get))
    assert a["blocked_pct"] == (12.5, None) and a["latency"] == (12.3, None), a
    assert vistos[-1][1]["Authorization"] == "Basic " + base64.b64encode(b"u:p").decode()
    assert val(read("paperless", "http://x", {"key": "t"}, get))["inbox"] == (3, "warn"), "documents waiting are a warning"
    k = val(read("uptime-kuma", "http://x", {"slug": "home"}, get))
    assert k == {"up": (1, "good"), "down": (1, "bad")}, k
    s = val(read("sonarr", "http://x", {"key": "s"}, get))
    assert s == {"wanted": (7, "warn"), "queued": (2, None), "series": (3, None)}, s
    assert val(read("radarr", "http://x", {"key": "s"}, get))["movies"] == (1, None)
    assert val(read("jellyfin", "http://x", {"key": "j"}, get)) == {"streams": (1, None), "movies": (40, None), "series": (9, None), "songs": (900, None)}
    class E(Exception):
        code = 401
    def nega(u, h=None):
        raise E()
    assert read("immich", "http://x", {"key": "bad"}, nega) == {"error": "HTTP 401"}, "a refused key is an error on the card"
    assert configured("adguard", {"user": "u", "password": ""}) is False and configured("immich", {"key": "k"}) is True
    assert slot("media-stack", {"type": "sonarr", "unit": "media-stack-sonarr"}) == "media-stack/media-stack-sonarr" and slot("immich", {"type": "immich"}) == "immich"
    assert set(FIELD_LABELS) >= {x for r in (val(read(t, "http://x", {"key": "k", "user": "u", "password": "p", "slug": "home"}, get)) for t in TYPES) for x in r}
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        save(tmp, {"immich": {"key": "k"}})
        assert load(tmp) == {"immich": {"key": "k"}} and oct(config_file(tmp).stat().st_mode)[-3:] == "600"
    print("svcwidgets selftest: ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else print(__doc__)
