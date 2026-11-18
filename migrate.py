#!/usr/bin/env python3
"""Moves an install made under an app the repository has since split, to the apps that replaced it.

`media-stack` was one folder of thirteen units: `media-stack-jellyfin`, `media-stack-sonarr`... sharing one volumes
folder and one `.env`. Each of them is an app of its own now (`jellyfin`, `sonarr`...), with its own data folder, its own
`.env` and the unit named after it. A host that installed the old one has units, data and settings under the old names
that nothing in the repository owns any more, and the new apps would collide with them (the container names are the
same). This module finds that and moves it:

- the data folder `volumes/media-stack/<name>` becomes `volumes/<name>` (a rename: nothing is copied or deleted);
- the settings `env/media-stack.env` is copied to `env/<name>.env` for each app that read it, and
  `env/media-stack-gluetun.env` becomes `env/gluetun.env`;
- the unit is written again from the repository, for the access rule it was installed with, under its new name, with
  its drop-ins (image pin, customization) moved beside it;
- a unit that was running is started again, one that was stopped stays stopped, one that was stopped on purpose (masked) stays masked.

It acts only on units it finds under the old names, and nothing else. The plan is shown first; `--apply` does it.

    python3 migrate.py --selftest
"""

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# old app -> {"units": {old unit: new app}, "volumes": old volumes folder, "envs": {old env file: [new apps that read it]}}
MIGRATIONS = {
    "media-stack": {
        "units": {f"media-stack-{n}": n for n in ("bazarr", "deluge", "dispatcharr", "downtify", "gluetun", "jellyfin", "lidarr",
                                                   "navidrome", "prowlarr", "radarr", "sabnzbd", "seerr", "sonarr")},
        "volumes": "media-stack",
        "envs": {"media-stack.env": ["bazarr", "deluge", "lidarr", "navidrome", "prowlarr", "radarr", "sabnzbd", "seerr", "sonarr"],
                 "media-stack-gluetun.env": ["gluetun"]},
    },
}


def systemd_dir(home):
    return Path(home) / ".config/containers/systemd"


def find_unit(home, unit):
    """The installed `<unit>.container` (loose or in a subfolder), or None."""
    return next(iter(systemd_dir(home).rglob(f"{unit}.container")), None)


def legacy(home):
    """[{"from", "units": [{"old", "new", "path", "active", "masked"}]}] for the old installs found on this host."""
    achados = []
    for velho, m in MIGRATIONS.items():
        unidades = []
        for unit, novo in sorted(m["units"].items()):
            p = find_unit(home, unit)
            if p is not None:
                unidades.append({"old": unit, "new": novo, "path": str(p)})
        if unidades:
            achados.append({"from": velho, "units": unidades})
    return achados


def legacy_for(home, app):
    """The old unit that stands where the app `app` would be installed, or None: installing both would collide."""
    for m in MIGRATIONS.values():
        for unit, novo in m["units"].items():
            if novo == app and find_unit(home, unit) is not None:
                return unit
    return None


def rewrite(texto, old_app, old_unit, new_app):
    """The old installed unit text as the new unit would read: the data folder and the settings file renamed. Only for
    recovering the access rule it was installed with (the new unit itself is written from the repository)."""
    m = MIGRATIONS[old_app]
    t = texto.replace(f"volumes/{m['volumes']}/{new_app}/", f"volumes/{new_app}/")
    t = t.replace(f"env/{old_unit}.env", f"env/{new_app}.env")
    for envfile in m["envs"]:
        if new_app in m["envs"][envfile]:
            t = t.replace(f"env/{envfile}", f"env/{new_app}.env")
    return t


def plan(home, old_app, *, I, active=None, masked=None, run=None):
    """[(description, callable)] to move `old_app`'s units; `I` is install.py (it knows how to write a unit).

    `active(unit)` and `masked(unit)` say what the host's systemd thinks (a sandbox has no systemd: nothing is running).
    `run(cmd)` acts on the host (the engine's own, which in a sandbox only says what it would do)."""
    active = active or (lambda u: False)
    masked = masked or (lambda u: False)
    run = run or (lambda cmd: None)
    if old_app not in MIGRATIONS:
        raise KeyError(old_app)
    m = MIGRATIONS[old_app]
    home = Path(home)
    vol_velho, env_dir = home / ".config/containers/volumes" / m["volumes"], home / ".config/containers/env"
    passos, ligar, mascarar = [], [], []

    for u in legacy(home):
        if u["from"] != old_app:
            continue
        for item in u["units"]:
            velho, novo, caminho = item["old"], item["new"], Path(item["path"])
            s = I.Service(novo, str(home) if home != Path.home() else None)
            fonte = s.source(f"{novo}.container")
            alvo = s.unit_dest / f"{novo}.container"
            esta_ativo, esta_mascarado = active(velho), masked(velho)
            # The access rule it was installed with, read from the old bytes as the new unit would carry them.
            with tempfile.TemporaryDirectory() as t:
                tmp = Path(t, f"{novo}.container")
                tmp.write_text(rewrite(caminho.read_text(), old_app, velho, novo))
                lido = I.installed_access(tmp, fonte)
            modo = lido[0] if lido and lido[0] else "tailnet"
            href = lido[1] if lido and lido[1] is not None else modo == "local"

            if esta_ativo:
                passos.append((f"systemctl --user stop {velho}", lambda v=velho: run(["systemctl", "--user", "stop", f"{v}.service"])))
            dado_velho, dado_novo = vol_velho / novo, home / ".config/containers/volumes" / novo
            if dado_velho.exists():
                if dado_novo.exists() and any(dado_novo.iterdir()):
                    passos.append((f"!  {dado_novo} already has data: {dado_velho} is left where it is", lambda: None))
                else:
                    passos.append((f"mv {dado_velho} -> {dado_novo}", lambda a=dado_velho, b=dado_novo: (b.parent.mkdir(parents=True, exist_ok=True),
                                                                                                          shutil.rmtree(b, ignore_errors=True) if b.exists() else None, os.rename(a, b))))
            for envfile, apps in m["envs"].items():
                if novo in apps and (env_dir / envfile).is_file() and not (env_dir / f"{novo}.env").exists():
                    mover = envfile != "media-stack.env"        # the shared one is copied: the others still read it
                    passos.append((f"{'mv' if mover else 'cp'} {env_dir / envfile} -> {env_dir / (novo + '.env')}",
                                   lambda a=env_dir / envfile, b=env_dir / f"{novo}.env", mv=mover: (shutil.move(a, b) if mv else shutil.copy2(a, b))))
            passos.append((f"write {alvo}  (from the repository, --access {modo}), and {velho} goes",
                           lambda f=fonte, d=alvo, vp=caminho, mo=modo, hr=href: (d.parent.mkdir(parents=True, exist_ok=True), I.write_unit(f, d, mo, hr))))
            drop_velho, drop_novo = caminho.parent / f"{velho}.container.d", alvo.parent / f"{novo}.container.d"
            if drop_velho.is_dir():
                passos.append((f"mv {drop_velho} -> {drop_novo}", lambda a=drop_velho, b=drop_novo: (b.parent.mkdir(parents=True, exist_ok=True), shutil.move(a, b))))
            passos.append((f"rm {caminho}", lambda p=caminho: p.unlink(missing_ok=True)))
            if esta_mascarado:
                mascarar.append((velho, novo))
            if esta_ativo:
                ligar.append(novo)
    sub = systemd_dir(home) / old_app
    passos.append((f"rmdir {sub} (when empty)", lambda: sub.is_dir() and not any(sub.iterdir()) and sub.rmdir()))
    passos.append((f"rmdir {vol_velho} (when empty)", lambda: vol_velho.is_dir() and not any(vol_velho.iterdir()) and vol_velho.rmdir()))
    passos.append(("systemctl --user daemon-reload", lambda: run(["systemctl", "--user", "daemon-reload"])))
    for velho, novo in mascarar:
        passos.append((f"systemctl --user unmask {velho}; mask {novo}", lambda v=velho, n=novo: (run(["systemctl", "--user", "unmask", f"{v}.service"]), run(["systemctl", "--user", "mask", f"{n}.service"]))))
    for novo in ligar:
        passos.append((f"systemctl --user start {novo}", lambda n=novo: run(["systemctl", "--user", "start", f"{n}.service"])))
    return passos


# -- selftest ---------------------------------------------------------------------------------------------

def selftest():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import install as I
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        sd = home / ".config/containers/systemd/media-stack"
        sd.mkdir(parents=True)
        # an old install: jellyfin (no env), sonarr (the shared env), gluetun (its own env), with data and drop-ins
        for n in ("jellyfin", "sonarr", "gluetun"):
            (sd / f"media-stack-{n}.container").write_text(f"[Container]\nImage=x/{n}\nVolume=%h/.config/containers/volumes/media-stack/{n}/config:/config:Z\n")
        (sd / "media-stack-sonarr.container.d").mkdir()
        (sd / "media-stack-sonarr.container.d/10-image.conf").write_text("[Container]\nImage=lscr.io/linuxserver/sonarr:4.0\n")
        for n in ("jellyfin", "sonarr"):
            d = home / ".config/containers/volumes/media-stack" / n / "config"
            d.mkdir(parents=True)
            (d / "data.db").write_text(n)
        env = home / ".config/containers/env"
        env.mkdir(parents=True)
        (env / "media-stack.env").write_text("PUID=1000\n")
        (env / "media-stack-gluetun.env").write_text("VPN=x\n")

        achado = legacy(home)
        assert len(achado) == 1 and [u["new"] for u in achado[0]["units"]] == ["gluetun", "jellyfin", "sonarr"], achado
        assert legacy_for(home, "sonarr") == "media-stack-sonarr" and legacy_for(home, "radarr") is None
        assert legacy(Path(tmp, "empty")) == []

        # the plan reads the host's state; nothing runs in this sandbox
        cmds = []
        passos = plan(home, "media-stack", I=I, active=lambda u: u == "media-stack-jellyfin", masked=lambda u: u == "media-stack-gluetun", run=cmds.append)
        descricoes = [d for d, _ in passos]
        assert any(d.startswith("mv ") and "volumes/media-stack/jellyfin" in d for d in descricoes), descricoes
        assert any(d.startswith("cp ") and "media-stack.env" in d and "sonarr.env" in d for d in descricoes), "the shared env is copied"
        assert any(d.startswith("mv ") and "media-stack-gluetun.env" in d for d in descricoes), "gluetun's own env is moved"
        for _, f in passos:
            f()
        s = lambda *p: home.joinpath(".config/containers", *p)
        assert (s("volumes/jellyfin/config/data.db")).read_text() == "jellyfin" and not s("volumes/media-stack").exists(), "data renamed, the old folder gone"
        assert s("env/sonarr.env").read_text() == "PUID=1000\n" and s("env/media-stack.env").exists(), "the shared env is kept for whoever still reads it"
        assert s("env/gluetun.env").read_text() == "VPN=x\n" and not s("env/media-stack-gluetun.env").exists()
        assert s("systemd/jellyfin.container").is_file() and "jellyfin" in s("systemd/jellyfin.container").read_text()
        assert "volumes/jellyfin/" in s("systemd/jellyfin.container").read_text(), "written from the repository, the new data folder"
        assert s("systemd/sonarr.container.d/10-image.conf").read_text().endswith("sonarr:4.0\n"), "the drop-in moves with it"
        assert not s("systemd/media-stack").exists() and legacy(home) == [], "nothing of the old install is left"
        assert ["systemctl", "--user", "stop", "media-stack-jellyfin.service"] in cmds and ["systemctl", "--user", "start", "jellyfin.service"] in cmds
        assert ["systemctl", "--user", "mask", "gluetun.service"] in cmds and ["systemctl", "--user", "unmask", "media-stack-gluetun.service"] in cmds
        assert not any(c[:3] == ["systemctl", "--user", "start"] and c[3] in ("sonarr.service", "gluetun.service") for c in cmds), "a stopped one stays stopped"
        # data that is already there is never overwritten
        d = home / ".config/containers/volumes/media-stack/bazarr"
        (d / "config").mkdir(parents=True)
        (d / "config/x").write_text("old")
        n_ = home / ".config/containers/volumes/bazarr/config"
        n_.mkdir(parents=True)
        (n_ / "y").write_text("new")
        (home / ".config/containers/systemd/media-stack-bazarr.container").write_text("[Container]\nImage=x\n")
        for _, f in plan(home, "media-stack", I=I):
            f()
        assert (n_ / "y").read_text() == "new" and (d / "config/x").read_text() == "old", "an existing data folder is left alone and so is the old one"
        try:
            plan(home, "nope", I=I)
            raise AssertionError("an unknown old app")
        except KeyError:
            pass
    print("migrate selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
