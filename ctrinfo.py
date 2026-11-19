#!/usr/bin/env python3
"""What Podman says about a container and about the images on the disk, shaped for the store.

The store is Quadlet-first and the repository is the source, so this is read-only: it explains what runs and why it is
unhealthy, and removes one unused image. It never creates a container outside a unit.

- `health_view`: the container's health, its last runs with what each printed, and the probe's own settings. The
  answer to "why is it unhealthy" is in the output of the last failing run.
- `runtime_view`: what actually runs (command, networks and addresses, ports, mounts, variables, the limits the unit
  asked for). It is the container as Podman has it, where Customize shows what the *unit* says. Variable values are
  masked unless asked for: a `Secret=` of type `env` shows up in a container's environment.
- `image_views` / `history_view`: every image with its size, which apps use it, the build date and the version/revision
  labels the image carries, and whether it can go (nothing uses it and no installed unit asks for it).

    python3 ctrinfo.py --selftest
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PODMAN = os.environ.get("QH_PODMAN", "podman")        # tests point it at a stand-in
MASK = "••••••••"
OUTPUT_MAX = 2000                                      # characters of a probe's output kept
LABELS = ("org.opencontainers.image.version", "org.opencontainers.image.revision", "org.opencontainers.image.created",
          "org.opencontainers.image.source", "org.opencontainers.image.documentation",
          "org.opencontainers.image.description", "org.opencontainers.image.title", "org.opencontainers.image.url")


def podman(*args, timeout=30):
    """(returncode, stdout, stderr) of a podman command."""
    r = subprocess.run([PODMAN, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def _seconds(ns):
    return round(ns / 1e9, 1) if isinstance(ns, (int, float)) and ns else None


def _short(texto, n=OUTPUT_MAX):
    texto = (texto or "").strip()
    return texto if len(texto) <= n else texto[:n] + "…"


# -- health ----------------------------------------------------------------------------------------------------

def health_view(raw):
    """{status, streak, runs: [{start, end, exit, output}] newest first, config: {...}} from one `podman inspect`."""
    h = (raw.get("State") or {}).get("Health") or {}
    cfg = (raw.get("Config") or {})
    hc = cfg.get("Healthcheck") or {}
    teste = hc.get("Test") or []
    acao = cfg.get("HealthcheckOnFailureAction")
    runs = [{"start": x.get("Start"), "end": x.get("End"), "exit": x.get("ExitCode"), "output": _short(x.get("Output"))}
            for x in (h.get("Log") or [])]
    return {"status": h.get("Status") or ("none" if not teste else "starting"), "streak": h.get("FailingStreak") or 0,
            "runs": list(reversed(runs)),
            "config": {"test": " ".join(teste[1:]) if teste and teste[0] in ("CMD-SHELL", "CMD") else " ".join(teste),
                       "shell": bool(teste) and teste[0] == "CMD-SHELL", "interval": _seconds(hc.get("Interval")),
                       "timeout": _seconds(hc.get("Timeout")), "start_period": _seconds(hc.get("StartPeriod")),
                       "retries": hc.get("Retries"), "on_failure": acao if acao and acao != "none" else None},
            "running": bool((raw.get("State") or {}).get("Running"))}


# -- runtime ---------------------------------------------------------------------------------------------------

def secret_env_keys(unit_text):
    """The variable names a unit fills from a podman secret (`Secret=name,type=env,target=VAR`)."""
    chaves = set()
    for m in re.finditer(r"^Secret\s*=\s*(.+)$", unit_text or "", re.M):
        opcoes = dict(p.split("=", 1) for p in m.group(1).split(",")[1:] if "=" in p)
        if opcoes.get("type") == "env" and opcoes.get("target"):
            chaves.add(opcoes["target"])
    return chaves


def runtime_view(raw, secret_keys=(), reveal=False):
    """What the container really is, from one `podman inspect`. Variable values are masked unless `reveal`."""
    st, cfg, hc = raw.get("State") or {}, raw.get("Config") or {}, raw.get("HostConfig") or {}
    ns = (raw.get("NetworkSettings") or {})
    redes = [{"name": n, "ip": v.get("IPAddress") or None, "gateway": v.get("Gateway") or None, "mac": v.get("MacAddress") or None,
              "aliases": [a for a in (v.get("Aliases") or []) if a != (raw.get("Id") or "")[:12]]}
             for n, v in sorted((ns.get("Networks") or {}).items())]
    portas = []
    for porta, ligacoes in sorted((ns.get("Ports") or {}).items()):
        cont, _, proto = porta.partition("/")
        for b in ligacoes or []:
            portas.append({"host_ip": b.get("HostIp") or "0.0.0.0", "host": b.get("HostPort"), "container": cont, "proto": proto or "tcp"})
    montagens = [{"type": m.get("Type"), "source": m.get("Source") or m.get("Name"), "dest": m.get("Destination"), "rw": bool(m.get("RW"))}
                 for m in raw.get("Mounts") or []]
    env = []
    for linha in sorted(cfg.get("Env") or []):
        k, _, v = linha.partition("=")
        env.append({"key": k, "value": v if reveal else (MASK if v else ""), "secret": k in set(secret_keys)})
    return {"name": (raw.get("Name") or "").lstrip("/"), "id": raw.get("Id"), "image": raw.get("ImageName"), "image_id": raw.get("Image"),
            "digest": raw.get("ImageDigest"), "status": st.get("Status"), "created": raw.get("Created"), "started": st.get("StartedAt"),
            "finished": st.get("FinishedAt") if not st.get("Running") else None, "restarts": raw.get("RestartCount") or 0,
            "exit_code": st.get("ExitCode"), "oom": bool(st.get("OOMKilled")),
            "command": " ".join([x for x in [raw.get("Path"), *(raw.get("Args") or [])] if x]),
            "entrypoint": cfg.get("Entrypoint"), "user": cfg.get("User") or None, "workdir": cfg.get("WorkingDir") or None,
            "networks": redes, "ports": portas, "mounts": montagens, "env": env, "revealed": bool(reveal),
            "limits": {"read_only": bool(hc.get("ReadonlyRootfs")), "pids": hc.get("PidsLimit") or None, "memory": hc.get("Memory") or None,
                       "cpus": round(hc["NanoCpus"] / 1e9, 2) if hc.get("NanoCpus") else None,
                       "cap_drop": hc.get("CapDrop") or [], "cap_add": hc.get("CapAdd") or [],
                       "security": [x for x in hc.get("SecurityOpt") or []], "userns": hc.get("UsernsMode") or None,
                       "restart": (hc.get("RestartPolicy") or {}).get("Name") or None}}


# -- images ----------------------------------------------------------------------------------------------------

def image_views(images, containers, wanted_names, wanted_digests, normalize, unit_of=None):
    """[{id, names, size, created, used_by, in_use, wanted, removable, labels}] largest first.

    One image can come back once per tag and is judged as ONE: in use under any name means in use, and its size counts
    once. `removable` means nothing uses it and no installed unit asks for it: the same "unused" as Resources."""
    unit_of = unit_of or (lambda nome: None)
    por_id = {}
    for im in images:
        g = por_id.setdefault(im["Id"], {"im": im, "names": [], "refs": set(), "dig": set()})
        g["names"] += [n for n in (im.get("Names") or []) if n not in g["names"]]
        g["refs"] |= {normalize(n) for n in (im.get("Names") or [])}
        g["dig"] |= {d.split("@")[-1] for d in (im.get("RepoDigests") or [])} | ({im["Digest"]} if im.get("Digest") else set())
    usam = {}
    for c in containers:
        for nome in c.get("Names") or []:
            usam.setdefault(c.get("ImageID"), []).append({"container": nome, "unit": unit_of(nome), "state": c.get("State")})
    saida = []
    for iid, g in por_id.items():
        im = g["im"]
        quem = usam.get(iid, [])
        pedida = bool(g["refs"] & wanted_names or g["dig"] & wanted_digests)
        rotulos = {k.rsplit(".", 1)[-1]: v for k, v in (im.get("Labels") or {}).items() if k in LABELS}
        saida.append({"id": iid, "short": iid[:12], "names": g["names"] or ["<none>"], "size": im.get("Size", 0),
                      "created": im.get("CreatedAt") or im.get("Created"), "used_by": quem, "in_use": bool(quem or im.get("Containers")),
                      "wanted": pedida, "removable": not (quem or im.get("Containers") or pedida), "labels": rotulos})
    saida.sort(key=lambda x: (-x["size"], x["id"]))
    return saida


def history_view(camadas):
    """[{created, by, size}] newest first, the command that made each layer trimmed."""
    return [{"created": c.get("created") or c.get("Created"), "by": _short(re.sub(r"^/bin/sh -c #\(nop\)\s*", "", c.get("CreatedBy") or ""), 300),
             "size": c.get("size", 0)} for c in camadas]


# -- selftest --------------------------------------------------------------------------------------------------

def selftest():
    raw = {"Id": "abcdef1234567890", "Name": "actual", "ImageName": "docker.io/x/actual:1", "Image": "img1", "ImageDigest": "sha256:aa",
           "Created": "2026-11-18T20:03:10-03:00", "Path": "tini", "Args": ["-g", "--", "node", "app.js"], "RestartCount": 2,
           "State": {"Status": "running", "Running": True, "StartedAt": "2026-11-18T20:03:11-03:00", "OOMKilled": False, "ExitCode": 0,
                     "Health": {"Status": "unhealthy", "FailingStreak": 3,
                                "Log": [{"Start": "t1", "End": "t1e", "ExitCode": 0, "Output": ""},
                                        {"Start": "t2", "End": "t2e", "ExitCode": 1, "Output": "curl: (7) refused\n" + "x" * 3000}]}},
           "Config": {"Env": ["PATH=/bin", "ADMIN_TOKEN=s3cret", "EMPTY="], "User": "1000", "WorkingDir": "/app", "Entrypoint": ["/usr/bin/tini"],
                      "Healthcheck": {"Test": ["CMD-SHELL", "node scripts/health-check.js"], "Interval": 60 * 10 ** 9, "Timeout": 10 * 10 ** 9,
                                      "StartPeriod": 20 * 10 ** 9, "Retries": 3}, "HealthcheckOnFailureAction": "kill"},
           "HostConfig": {"ReadonlyRootfs": True, "PidsLimit": 256, "Memory": 0, "NanoCpus": 0, "CapDrop": ["CAP_CHOWN"], "CapAdd": [],
                          "SecurityOpt": ["no-new-privileges"], "UsernsMode": "", "RestartPolicy": {"Name": "no"}},
           "Mounts": [{"Type": "bind", "Source": "/h/data", "Destination": "/data", "RW": True}, {"Type": "bind", "Source": "/h/lib", "Destination": "/lib", "RW": False}],
           "NetworkSettings": {"Networks": {"tsdproxy-net": {"IPAddress": "10.89.0.2", "Gateway": "10.89.0.1", "MacAddress": "aa:bb", "Aliases": ["abcdef123456", "actual"]}},
                               "Ports": {"5006/tcp": [{"HostIp": "", "HostPort": "5006"}], "9000/tcp": None}}}
    h = health_view(raw)
    assert h["status"] == "unhealthy" and h["streak"] == 3 and [r["exit"] for r in h["runs"]] == [1, 0], h["runs"]
    assert h["runs"][0]["output"].startswith("curl: (7) refused") and len(h["runs"][0]["output"]) <= OUTPUT_MAX + 1, "long output is cut"
    assert h["config"] == {"test": "node scripts/health-check.js", "shell": True, "interval": 60.0, "timeout": 10.0, "start_period": 20.0,
                           "retries": 3, "on_failure": "kill"}, h["config"]
    assert health_view({"State": {}, "Config": {}})["status"] == "none", "a container with no probe"
    assert health_view({"State": {}, "Config": {"HealthcheckOnFailureAction": "none", "Healthcheck": {"Test": ["CMD", "a", "b"]}}})["config"]["on_failure"] is None

    assert secret_env_keys("Secret=a,type=env,target=ADMIN_TOKEN\nSecret=b,target=/run/secrets/b\nSecret=c,type=mount,target=/x\n") == {"ADMIN_TOKEN"}
    r = runtime_view(raw, {"ADMIN_TOKEN"})
    env = {e["key"]: e for e in r["env"]}
    assert env["ADMIN_TOKEN"]["value"] == MASK and env["ADMIN_TOKEN"]["secret"] is True and env["PATH"]["value"] == MASK, "values are masked"
    assert env["EMPTY"]["value"] == "" and r["revealed"] is False
    assert {e["key"]: e["value"] for e in runtime_view(raw, {"ADMIN_TOKEN"}, reveal=True)["env"]}["ADMIN_TOKEN"] == "s3cret"
    assert r["command"] == "tini -g -- node app.js" and r["networks"] == [{"name": "tsdproxy-net", "ip": "10.89.0.2", "gateway": "10.89.0.1", "mac": "aa:bb", "aliases": ["actual"]}], r["networks"]
    assert r["ports"] == [{"host_ip": "0.0.0.0", "host": "5006", "container": "5006", "proto": "tcp"}], "an unpublished port is not listed"
    assert [(m["dest"], m["rw"]) for m in r["mounts"]] == [("/data", True), ("/lib", False)]
    assert r["limits"]["read_only"] and r["limits"]["pids"] == 256 and r["limits"]["memory"] is None and r["restarts"] == 2 and r["name"] == "actual"

    imgs = [{"Id": "i1", "Names": ["docker.io/x/a:1"], "Size": 100, "Created": 5, "CreatedAt": "2026-01-01T00:00:00Z", "Containers": 0, "Digest": "sha256:d1",
             "RepoDigests": ["docker.io/x/a@sha256:d1"], "Labels": {"org.opencontainers.image.version": "1.0", "other": "x"}},
            {"Id": "i1", "Names": ["docker.io/x/a:latest"], "Size": 100, "Containers": 0, "Digest": "sha256:d1", "RepoDigests": []},
            {"Id": "i2", "Names": ["docker.io/x/b:2"], "Size": 300, "Containers": 1, "Labels": None},
            {"Id": "i3", "Names": ["docker.io/x/c:3"], "Size": 50, "Containers": 0, "Labels": {}},
            {"Id": "i4", "Names": [], "Size": 10, "Containers": 0}]
    ctrs = [{"Names": ["b"], "ImageID": "i2", "State": "running"}]
    v = image_views(imgs, ctrs, {"docker.io/x/a:1"}, set(), lambda r: r if "/" in r else "docker.io/library/" + r, lambda n: "b-unit" if n == "b" else None)
    por = {x["id"]: x for x in v}
    assert [x["id"] for x in v] == ["i2", "i1", "i3", "i4"] and len(v) == 4, "one row per image, largest first"
    assert por["i1"]["names"] == ["docker.io/x/a:1", "docker.io/x/a:latest"] and por["i1"]["wanted"] and not por["i1"]["removable"], "a unit asks for it"
    assert por["i1"]["labels"] == {"version": "1.0"} and por["i1"]["created"] == "2026-01-01T00:00:00Z"
    assert por["i2"]["in_use"] and por["i2"]["used_by"][0]["unit"] == "b-unit" and not por["i2"]["removable"]
    assert por["i3"]["removable"] and por["i4"]["names"] == ["<none>"] and por["i4"]["removable"]
    assert history_view([{"created": "t", "CreatedBy": "/bin/sh -c #(nop)  CMD [\"node\"]", "size": 7}])[0] == {"created": "t", "by": "CMD [\"node\"]", "size": 7}
    print("ctrinfo selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
