#!/usr/bin/env python3
"""Local customization of an installed unit, as a Quadlet drop-in.

The unit stays the repository's. What a person changes — a port, a volume, a
variable, a device, a capability, the restart policy — goes into
`<unit>.container.d/50-store.conf` next to it. `qh --update` rewrites the unit
and leaves the drop-in alone, and going back is deleting one file.

How a drop-in says "not what the unit says": Quadlet keeps every `PublishPort=`,
`Volume=`, `Environment=`, `AddDevice=` and `AddCapability=` of both files, so
to CHANGE a list rather than add to it, the drop-in resets it with an empty
assignment and lists what it wants. That was measured on Podman 6.1.4, not
assumed. `[Service] Restart=` is single-valued: the later one wins.

What this module will not do is as deliberate as what it does. Whoever holds the
store's token can already install what the repository offers; letting the same
token mount any host path, add any capability or turn on `--privileged` would
make it a shell on the host. So a NEW volume must sit inside a root the person
named (default: the containers' own volumes folder), a NEW capability must be on
a short list, and there is no privileged switch and no image or tag field —
versions belong to the repository (rule 9). An entry the unit already carries is
always accepted as it is: this guards what is added, not what the repository
shipped.

Memory and CPU limits are here only when they can work. Rootless, the controllers are usable
only when the user's systemd delegates them (`cgroup.controllers` of `user@.service` lists
`memory` and `cpu`); on a host that does not, `--memory` makes the container fail to start
(`memory.swap.max: no such file or directory`), so saving one is refused there, with the reason.
Memory is Quadlet's `Memory=`; CPU is `PodmanArgs=--cpus=N`, which has no key of its own.

Pure functions, so it is tested without a host:

    python3 overrides.py --selftest
"""

import hashlib
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DROPIN = "50-store.conf"
# (group, Quadlet key) — all in [Container]. Restart is [Service] and handled apart.
GROUPS = (("ports", "PublishPort"), ("volumes", "Volume"), ("env", "Environment"),
          ("devices", "AddDevice"), ("caps", "AddCapability"))
RESTARTS = ("always", "on-failure", "on-abnormal", "on-abort", "on-success", "no")
# What a new capability may be. Podman's eleven defaults, plus the ones a service
# commonly asks for. SYS_ADMIN, NET_ADMIN, SYS_PTRACE and the like are left out:
# for those, edit the unit by hand — that is a decision, not a form field.
CAPS_OK = ("CHOWN", "DAC_OVERRIDE", "FOWNER", "FSETID", "KILL", "NET_BIND_SERVICE", "NET_RAW",
           "SETFCAP", "SETGID", "SETPCAP", "SETUID", "SYS_CHROOT", "SYS_NICE", "MKNOD", "AUDIT_WRITE")
ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
CONTAINER_PATH = re.compile(r"^/[A-Za-z0-9._@+/-]*$")
DEVICE = re.compile(r"^/dev/[A-Za-z0-9._/-]+(:/dev/[A-Za-z0-9._/-]+)?(:[rwm]{1,3})?$")
CDI = re.compile(r"^[A-Za-z0-9.-]+/[A-Za-z0-9_-]+=[A-Za-z0-9._-]+$")
PORT = re.compile(r"^(?:(?P<bind>\[[0-9a-fA-F:]+\]|[0-9.]+):)?(?P<host>\d{1,5}):(?P<container>\d{1,5})"
                  r"(?:/(?P<proto>tcp|udp))?$")
# An image reference: registry[:port]/path[:tag][@digest], lowercase paths as registries require.
IMAGE_REF = re.compile(r"^(?:[a-z0-9.-]+(?::\d+)?/)?[a-z0-9._-]+(?:/[a-z0-9._-]+)*(?::[A-Za-z0-9_][A-Za-z0-9._-]{0,127})?(?:@sha256:[0-9a-f]{64})?$")
LIMIT_VALUE = 4096


# -- reading a unit ---------------------------------------------------------------

def parse_sections(text):
    """{section: [(key, value)]} in file order. Comments and blank lines are skipped."""
    saida, atual = {}, None
    for linha in text.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith(("#", ";")):
            continue
        if linha.startswith("[") and linha.endswith("]"):
            atual = linha[1:-1]
            saida.setdefault(atual, [])
            continue
        chave, sep, valor = linha.partition("=")
        if sep and atual is not None:
            saida[atual].append((chave.strip(), valor.strip()))
    return saida


def _cap(token):
    t = token.strip().upper()
    return t[4:] if t.startswith("CAP_") else t


def _aplica(listas, secoes):
    """Applies a file's lines to `listas` the way Quadlet does; returns its Restart, if any."""
    for grupo, chave in GROUPS:
        for k, v in secoes.get("Container", []):
            if k != chave:
                continue
            if v == "":
                listas[grupo] = []
            elif grupo == "caps":
                listas[grupo] += [_cap(x) for x in v.split()]
            else:
                listas[grupo].append(v)
    restart = None
    for k, v in secoes.get("Service", []):
        if k == "Restart" and v:
            restart = v
    return restart


def lists_of(sections):
    """({group: [raw]}, restart) as Quadlet would assemble them: an empty value resets the list."""
    listas = {g: [] for g, _ in GROUPS}
    return listas, _aplica(listas, sections)


def base_of(unit_text):
    return lists_of(parse_sections(unit_text))


def merged(base, dropin_text):
    """What a unit and its drop-in come to, by Quadlet's own rules."""
    if not dropin_text:
        return base
    listas = {g: list(v) for g, v in base[0].items()}
    restart = _aplica(listas, parse_sections(dropin_text))
    return listas, restart or base[1]


def base_hash(base):
    """Short fingerprint of the lists a drop-in may have reset.

    A drop-in that resets a list hides whatever the repository adds to it later.
    The hash recorded in the file is how the store notices the unit moved under
    a customization and says so, instead of leaving the difference silent.
    """
    return hashlib.sha256(json.dumps([base[0], base[1]], sort_keys=True).encode()).hexdigest()[:16]


# -- limits: Memory= and --cpus -------------------------------------------------------

MEMORIA = re.compile(r"^(\d+(?:\.\d+)?)([kmg]?)b?$", re.I)
CPUS = re.compile(r"^\d+(?:\.\d{1,2})?$")
MEMORIA_MIN = 16 * 1024 * 1024               # below this a container does not get to run anything


def limits_in(sections):
    """{memory, cpus} a unit (or a drop-in) sets: the last `Memory=`, and a `--cpus` inside any `PodmanArgs=`."""
    mem = cpus = ""
    for k, v in sections.get("Container", []):
        if k == "Memory":
            mem = v
        elif k == "PodmanArgs":
            m = re.search(r"--cpus[= ](\d+(?:\.\d+)?)", v)
            if m:
                cpus = m.group(1)
    return {"memory": mem, "cpus": cpus}


def merged_limits(base_text, dropin_text):
    """What a unit and its drop-in come to for the two limits; the drop-in wins, as it does in Quadlet."""
    b = limits_in(parse_sections(base_text))
    d = limits_in(parse_sections(dropin_text)) if dropin_text else {"memory": "", "cpus": ""}
    return {k: d[k] or b[k] for k in b}


def memory_bytes(texto):
    """Bytes in `512m`, `2g`, `1.5G`, `256mb`; None when it is not a memory size."""
    m = MEMORIA.match((texto or "").strip())
    if not m:
        return None
    return int(float(m.group(1)) * {"": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}[m.group(2).lower()])


# -- values -----------------------------------------------------------------------

def unescape_value(raw):
    """The real value behind systemd's quoting and its `$$` and `%%`."""
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        interior, out, i = v[1:-1], [], 0
        while i < len(interior):
            c = interior[i]
            if c == "\\" and i + 1 < len(interior):
                n = interior[i + 1]
                if n in '"\\':
                    out.append(n); i += 2; continue
                if n == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", interior[i + 2:i + 4]):
                    out.append(chr(int(interior[i + 2:i + 4], 16))); i += 4; continue
            out.append(c); i += 1
        v = "".join(out)
    return v.replace("$$", "$").replace("%%", "%")


def escape_value(valor):
    """A value as the unit file must carry it. Quadlet escapes spaces and quotes on its own,
    but leaves `$` and `%` for systemd to expand — so they are doubled here, the way
    rule 7 of the conventions asks for in HealthCmd."""
    q = valor.replace("\\", "\\\\").replace('"', '\\"').replace("$", "$$").replace("%", "%%")
    return q if q and re.fullmatch(r"[A-Za-z0-9_./:@+,=$%-]*", q) else f'"{q}"'


# -- items: the form's view of one entry, and the line it becomes -------------------

def parse_item(grupo, raw):
    """A raw line as a dict the form can edit; `opaque` when it is not a plain shape."""
    if grupo == "ports":
        m = PORT.match(raw)
        if m:
            return {"bind": m["bind"] or "", "host": int(m["host"]), "container": int(m["container"]),
                    "proto": m["proto"] or "tcp"}
    elif grupo == "volumes":
        partes = raw.split(":")
        if len(partes) in (2, 3) and partes[0] and partes[1]:
            opts = [o for o in (partes[2].split(",") if len(partes) == 3 else []) if o]
            return {"host": partes[0], "container": partes[1],
                    "label": "Z" if "Z" in opts else "z" if "z" in opts else "",
                    "ro": "ro" in opts, "extra": [o for o in opts if o not in ("Z", "z", "ro", "rw")]}
    elif grupo == "env":
        chave, sep, valor = raw.partition("=")
        if sep and ENV_KEY.match(chave.strip()):
            return {"key": chave.strip(), "value": unescape_value(valor)}
    elif grupo == "devices":
        return {"path": raw}
    elif grupo == "caps":
        return {"name": _cap(raw)}
    return {"raw": raw, "opaque": True}


def render_item(grupo, item):
    """The line an item stands for. An opaque one is its raw text, untouched."""
    if item.get("opaque") or "raw" in item:
        return item["raw"]
    if grupo == "ports":
        return (f"{item['bind'] + ':' if item.get('bind') else ''}{item['host']}:{item['container']}"
                + ("/udp" if item.get("proto") == "udp" else ""))
    if grupo == "volumes":
        opts = ([item["label"]] if item.get("label") else []) + (["ro"] if item.get("ro") else []) \
            + list(item.get("extra") or [])
        return f"{item['host']}:{item['container']}" + (":" + ",".join(opts) if opts else "")
    if grupo == "env":
        return f"{item['key']}={escape_value(item['value'])}"
    if grupo == "devices":
        return item["path"]
    return item["name"]


def describe(listas):
    """{group: [item]} for the form, from raw lists."""
    return {g: [parse_item(g, r) for r in listas[g]] for g, _ in GROUPS}


def canon(grupo, raw):
    """The raw line as `render_item` would write it — so a base line and the same entry
    coming back from the form compare equal even when the spelling differs."""
    return render_item(grupo, parse_item(grupo, raw))


# -- the rules for what is NEW ---------------------------------------------------------

def under(path, roots):
    """Whether `path` is strictly inside one of `roots`, after symlinks are followed."""
    real = os.path.realpath(path)
    for r in roots:
        r = os.path.realpath(r)
        if real != r and real.startswith(r.rstrip("/") + "/"):
            return True
    return False


def resolve_host(path, home, var=None):
    """`%h` and `${VAR}` made concrete for checking; None when something cannot be resolved."""
    p = path.replace("%h", str(home))
    for nome in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", p):
        valor = (var or (lambda _n: ""))(nome)
        if not valor:
            return None
        p = p.replace("${" + nome + "}", valor)
    return p


class Contexto:
    """What validation needs to know about the host, passed in so it can be faked."""

    def __init__(self, home, roots=(), floor=1024, em_uso=None, escutando=None, existe=os.path.exists,
                 var=None, limits_ok=None, mem_total=0, ncpu=0):
        self.home, self.roots, self.floor = Path(home), list(roots), floor
        self.limits_ok = limits_ok or {"memory": False, "cpu": False}   # which controllers the user's systemd delegates
        self.mem_total, self.ncpu = mem_total, ncpu
        self.em_uso = em_uso or {}              # {(host port, proto): unit that publishes it}
        self.escutando = escutando or set()     # {(port, proto)} bound on the host right now
        self.existe, self.var = existe, var


def _valida_porta(it, ctx, propria, erros):
    try:
        if it["bind"]:
            ipaddress.ip_address(it["bind"].strip("[]"))
    except ValueError:
        erros.append(f"porta {it['host']}: o endereço {it['bind']!r} não é um IP")
        return
    if not (1 <= it["container"] <= 65535):
        erros.append(f"porta do container {it['container']} fora de 1–65535")
    if not (ctx.floor <= it["host"] <= 65535):
        erros.append(f"porta {it['host']}: sem root o Podman só publica a partir da {ctx.floor}")
        return
    chave = (it["host"], it["proto"])
    dono = ctx.em_uso.get(chave)
    if dono and dono != propria:
        erros.append(f"porta {it['host']}/{it['proto']} já é publicada por {dono}")
    elif chave in ctx.escutando:
        erros.append(f"porta {it['host']}/{it['proto']} já está em uso neste host")


def _valida_volume(it, ctx, erros):
    host = it["host"]
    if re.search(r"[\s:%$\"']", host) and not re.fullmatch(r"(%h|\$\{[A-Za-z_]\w*\})[^\s:\"'%$]*", host):
        erros.append(f"volume {host!r}: o caminho não pode ter espaço, dois-pontos, % nem $")
        return
    real = resolve_host(host, ctx.home, ctx.var)
    if not real or not real.startswith("/"):
        erros.append(f"volume {host!r}: o caminho de origem não é absoluto nem resolvível")
        return
    if ".." in Path(real).parts:
        erros.append(f"volume {host!r}: sem '..' no caminho")
        return
    if not under(real, ctx.roots):
        erros.append(f"volume {host!r}: fora das pastas permitidas ({', '.join(ctx.roots) or 'nenhuma'}). "
                     f"Para liberar outra, escreva o caminho em ~/.config/quadlet-homelab/store-roots")
    if not CONTAINER_PATH.match(it["container"]) or it["container"] == "/" or ".." in it["container"].split("/"):
        erros.append(f"volume: o destino {it['container']!r} no container não é um caminho válido")
    if it.get("label") not in ("", "Z", "z"):
        erros.append("volume: o rótulo SELinux é Z (privado) ou z (compartilhado)")
    if it.get("extra"):
        erros.append("volume: só as opções Z, z, ro e rw são aceitas")


def _valida_item(grupo, it, ctx, propria, erros):
    if it.get("opaque") or "raw" in it:
        erros.append(f"{grupo}: {it.get('raw', '?')!r} não vem da unit e não é uma forma que o formulário aceita")
    elif grupo == "ports":
        _valida_porta(it, ctx, propria, erros)
    elif grupo == "volumes":
        _valida_volume(it, ctx, erros)
    elif grupo == "env":
        if not ENV_KEY.match(it["key"]):
            erros.append(f"variável {it['key']!r}: só letras, números e _, sem começar por número")
        elif len(it["value"]) > LIMIT_VALUE or re.search(r"[\r\n\x00]", it["value"]):
            erros.append(f"variável {it['key']}: o valor tem de ter uma linha só, com até {LIMIT_VALUE} caracteres")
    elif grupo == "devices":
        if not (DEVICE.match(it["path"]) or CDI.match(it["path"])):
            erros.append(f"dispositivo {it['path']!r}: use /dev/... ou um nome CDI")
        elif it["path"].startswith("/dev/") and not ctx.existe(it["path"].split(":")[0]):
            erros.append(f"dispositivo {it['path']}: não existe neste host")
    elif grupo == "caps":
        if it["name"] not in CAPS_OK:
            erros.append(f"capability {it['name']}: fora da lista permitida; para outra, edite a unit à mão")


def _chave_dup(grupo, item, linha):
    """What makes two entries of a group the same one: a host port, a destination, a name."""
    if item.get("opaque") or "raw" in item:
        return linha
    return {"ports": (item.get("host"), item.get("proto")), "volumes": item.get("container"),
            "env": item.get("key")}.get(grupo, linha)


def validate_and_render(base, desejado, restart, ctx, propria="", base_limits=None, base_image="", base_network="", redes=None):
    """(text or None, errors, warnings).

    `desejado` is {group: [item]} — the whole list the person wants for each group.
    A group equal to the base's is not written; one that differs is written as a
    reset plus the full list. An item the base already carries is let through
    as it is, and only the rest is checked. text is None when nothing differs.
    """
    b_listas, b_restart = base
    erros, avisos, linhas = [], [], []
    for grupo, chave in GROUPS:
        itens = desejado.get(grupo)
        if itens is None:
            continue
        pedido = [render_item(grupo, i) for i in itens]
        original = [canon(grupo, r) for r in b_listas[grupo]]
        if pedido == original:
            continue
        conhecidos = set(original)
        vistos = set()
        for item, linha in zip(itens, pedido):
            if linha not in conhecidos:
                _valida_item(grupo, item, ctx, propria, erros)
            dup = _chave_dup(grupo, item, linha)
            if dup in vistos:
                erros.append(f"{grupo}: {dup} aparece duas vezes")
            vistos.add(dup)
        linhas += [(chave, "")] + [(chave, l) for l in pedido]
        if grupo == "ports" and any(l not in conhecidos for l in pedido):
            avisos.append("uma porta publicada abre o app na rede local, qualquer que seja a regra de acesso")
    # Limits: compared with what the unit itself carries, like the lists. A value that differs is
    # checked, and refused outright where the controller is not delegated: it would not start.
    pedido_lim = desejado.get("limits") or {}
    base_lim = base_limits or {"memory": "", "cpus": ""}
    mem = str(pedido_lim.get("memory") or "").strip().lower()
    cpus = str(pedido_lim.get("cpus") or "").strip()
    if mem != base_lim["memory"].strip().lower():
        if not mem:
            erros.append("memória: o limite vem da própria unit; para tirá-lo, edite a unit à mão")
        elif not ctx.limits_ok.get("memory"):
            erros.append("memória: o systemd do seu usuário não delega o controlador memory; com um limite o container não sobe")
        elif (b := memory_bytes(mem)) is None:
            erros.append(f"memória {mem!r}: use um número com k, m ou g (512m, 2g)")
        elif b < MEMORIA_MIN:
            erros.append("memória: o mínimo é 16m")
        elif ctx.mem_total and b > ctx.mem_total:
            erros.append(f"memória {mem}: mais do que este host tem")
        else:
            linhas.append(("Memory", mem))
    if cpus != base_lim["cpus"].strip():
        if not cpus:
            erros.append("CPUs: o limite vem da própria unit; para tirá-lo, edite a unit à mão")
        elif not ctx.limits_ok.get("cpu"):
            erros.append("CPUs: o systemd do seu usuário não delega o controlador cpu; com um limite o container não sobe")
        elif not CPUS.match(cpus) or float(cpus) < 0.1:
            erros.append(f"CPUs {cpus!r}: use um número a partir de 0.1 (1.5 é um núcleo e meio)")
        elif ctx.ncpu and float(cpus) > ctx.ncpu:
            erros.append(f"CPUs {cpus}: este host tem {ctx.ncpu}")
        else:
            linhas.append(("PodmanArgs", f"--cpus={cpus}"))
    # The image: only when the person set one that is not the unit's own (an empty field leaves the unit, and the version
    # the host pins for it, alone).
    imagem = str(desejado.get("image") or "").strip()
    if imagem and imagem != (base_image or "").strip():
        if len(imagem) > 300 or not IMAGE_REF.match(imagem):
            erros.append(f"imagem {imagem!r}: use o endereço como registry/organização/nome:tag")
        elif ":" not in imagem.rsplit("/", 1)[-1] and "@" not in imagem:
            erros.append("imagem: sem tag nem digest o Podman usa :latest; escreva a versão (a regra 9 não aceita tag flutuante)")
        else:
            linhas.append(("Image", imagem))
    # The network: one of the networks that exist (a `.network` unit), when it is not the one the unit joins. Quadlet's list key is reset
    # first, so it replaces the unit's own rather than adding to it.
    rede = str(desejado.get("network") or "").strip()
    if rede and rede != (base_network or "").strip():
        if redes is None or rede not in redes:
            erros.append(f"rede {rede!r}: use uma das redes que existem ({', '.join(sorted(redes or [])) or 'nenhuma encontrada'})")
        else:
            linhas += [("Network", ""), ("Network", rede)]
            avisos.append("trocar a rede tira o app da rede do tsdproxy, se estava nela: o endereço da tailnet deixa de funcionar")
    if restart is not None and restart != (b_restart or ""):
        if restart not in RESTARTS:
            erros.append(f"reinício {restart!r}: use {', '.join(RESTARTS)}")
    if erros:
        return None, erros, avisos
    servico = restart is not None and restart != (b_restart or "")
    if not linhas and not servico:
        return None, [], avisos
    saida = ["# Written by qh-store. This file is replaced when you save again; delete it, or use",
             "# Revert in the store, to go back to the unit exactly as the repository publishes it.",
             f"# base={base_hash(base)}"]
    if linhas:
        saida += ["[Container]"] + [f"{k}={v}" for k, v in linhas]
    if servico:
        saida += ["[Service]", f"Restart={restart}"]
    return "\n".join(saida) + "\n", [], avisos


def recorded_base(dropin_text):
    m = re.search(r"^# base=([0-9a-f]{16})$", dropin_text or "", re.M)
    return m.group(1) if m else None


# -- files --------------------------------------------------------------------------

def dropin_path(unit_path):
    unit_path = Path(unit_path)
    return unit_path.parent / (unit_path.name + ".d") / DROPIN


def read_override(unit_path):
    p = dropin_path(unit_path)
    return p.read_text() if p.is_file() else None


def write_override(unit_path, texto):
    """Atomic, and private: a variable may carry a key."""
    p = dropin_path(unit_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(texto)
    tmp.replace(p)


def remove_override(unit_path):
    p = dropin_path(unit_path)
    if p.is_file():
        p.unlink()
    try:
        p.parent.rmdir()          # only when it is empty: another drop-in there is not ours to remove
    except OSError:
        pass


# -- what Quadlet itself says ------------------------------------------------------------

def quadlet_binary():
    for c in ("/usr/libexec/podman/quadlet", "/usr/lib/podman/quadlet", "/usr/lib/systemd/user-generators/podman-user-generator"):
        if os.access(c, os.X_OK):
            return c
    return shutil.which("quadlet")


def quadlet_check(systemd_dir, unit_path, dropin_text):
    """(ok, messages, generated ExecStart) from the host's own generator on a scratch copy.

    ok is None when there is no generator to ask. The copy is the whole tree, so
    references between units resolve; only the errors that name THIS unit count,
    because another unit's problem is not a reason to refuse this change.
    The generator checks keys, not values: a port that is not a number gets through
    it, which is why the rules above exist.
    """
    binario = quadlet_binary()
    if not binario:
        return None, [], ""
    systemd_dir, unit_path = Path(systemd_dir), Path(unit_path)
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "units"
        shutil.copytree(systemd_dir, copia, symlinks=False, ignore=shutil.ignore_patterns("*.tmp"))
        alvo = copia / unit_path.relative_to(systemd_dir)
        d = alvo.parent / (alvo.name + ".d")
        if dropin_text is None:
            shutil.rmtree(d, ignore_errors=True)
        else:
            d.mkdir(exist_ok=True)
            (d / DROPIN).write_text(dropin_text)
        r = subprocess.run([binario, "-dryrun", "-user"], capture_output=True, text=True,
                           env={**os.environ, "QUADLET_UNIT_DIRS": str(copia)}, timeout=60)
    nome = unit_path.name
    problemas = [re.sub(r"^quadlet-generator\[\d+\]:\s*", "", l).replace(str(copia), "")
                 for l in r.stderr.splitlines() if f'"{nome}"' in l and "converting" in l]
    gerado = ""
    achou = False
    for linha in r.stdout.splitlines():
        if linha.startswith("---") and nome[:-len(".container")] in linha:
            achou = True
        if achou and linha.startswith("ExecStart="):
            gerado = linha[len("ExecStart="):]
            break
    return (not problemas), problemas, gerado


# -- self-test -------------------------------------------------------------------------

DEMO = """[Unit]
Description=demo

[Container]
Image=docker.io/library/busybox:1
ContainerName=demo
PublishPort=8085:3000
PublishPort=127.0.0.1:9000:9000/udp
Volume=%h/a:/a:Z
Volume=%h/b:/b:ro,z
Environment=A=1
Environment=B="two words"
AddCapability=CHOWN
AddCapability=CAP_SETUID SETGID
AddDevice=/dev/null

[Service]
Restart=always
"""


def selftest():
    ctx = Contexto("/home/u", roots=["/tmp"], existe=lambda p: p in ("/dev/null", "/dev/dri"))
    base = base_of(DEMO)
    assert base[0]["ports"] == ["8085:3000", "127.0.0.1:9000:9000/udp"] and base[1] == "always"
    assert base[0]["caps"] == ["CHOWN", "SETUID", "SETGID"], "CAP_ prefix dropped, one line may list several"
    assert describe(base[0])["env"][1] == {"key": "B", "value": "two words"}, "quotes read back"

    # the merge rule: an empty value resets the list, later lines add, the later Restart wins
    efetivo = merged(base, "[Container]\nPublishPort=\nPublishPort=9999:3000\nAddCapability=KILL\n[Service]\nRestart=on-failure\n")
    assert efetivo[0]["ports"] == ["9999:3000"] and efetivo[0]["caps"] == ["CHOWN", "SETUID", "SETGID", "KILL"]
    assert efetivo[0]["volumes"] == base[0]["volumes"] and efetivo[1] == "on-failure"

    # values: the escape is the systemd one, and it round-trips
    for v in ("simple", "two words", 'say "hi"', "a$b", "100%", "back\\slash", "", "x=y"):
        assert unescape_value(escape_value(v)) == v, v
    assert escape_value("a$b") == "a$$b" and escape_value("100%") == "100%%" and escape_value("x y") == '"x y"'

    # nothing changed -> no file; the base's own entries are never re-checked
    nada = {g: describe(base[0])[g] for g, _ in GROUPS}

    # limits: parsed from a unit and a drop-in, checked against what the host delegates, rendered as Memory= and --cpus
    assert memory_bytes("512m") == 512 * 1024 ** 2 and memory_bytes("2G") == 2 * 1024 ** 3 and memory_bytes("1.5g") == int(1.5 * 1024 ** 3)
    assert memory_bytes("256mb") == 256 * 1024 ** 2 and memory_bytes("lots") is None and memory_bytes("") is None
    assert limits_in(parse_sections("[Container]\nMemory=1g\nPodmanArgs=--shm-size=1g --cpus=2\n")) == {"memory": "1g", "cpus": "2"}
    assert limits_in(parse_sections("[Container]\nImage=x\n")) == {"memory": "", "cpus": ""}
    assert merged_limits("[Container]\nMemory=1g\n", "[Container]\nMemory=2g\nPodmanArgs=--cpus=1.5\n") == {"memory": "2g", "cpus": "1.5"}
    livre = Contexto("/home/u", roots=["/tmp"], limits_ok={"memory": True, "cpu": True}, mem_total=8 * 1024 ** 3, ncpu=4)
    sem = {"memory": "", "cpus": ""}
    quer = lambda **kw: {**nada, "limits": {**sem, **kw}}
    t, e, _ = validate_and_render(base, quer(memory="512m", cpus="1.5"), None, livre, base_limits=sem)
    assert not e and "Memory=512m" in t and "PodmanArgs=--cpus=1.5" in t, (e, t)
    assert validate_and_render(base, quer(), None, livre, base_limits=sem) == (None, [], []), "no limit asked: nothing written"
    assert validate_and_render(base, quer(memory="1g"), None, livre, base_limits={"memory": "1g", "cpus": ""}) == (None, [], []), "the unit's own limit is not a change"
    # the image: written only when it differs from the unit's, with a tag or a digest, and shaped like a reference
    img = lambda ref: {**nada, "image": ref}
    t, e, _ = validate_and_render(base, img("ghcr.io/o/r:1.2.0"), None, livre, base_limits=sem, base_image="ghcr.io/o/r")
    assert not e and "[Container]" in t and "Image=ghcr.io/o/r:1.2.0" in t, (e, t)
    assert validate_and_render(base, img("ghcr.io/o/r:1.2.0"), None, livre, base_limits=sem, base_image="ghcr.io/o/r:1.2.0") == (None, [], []), "the unit's own image is not a change"
    assert validate_and_render(base, img(""), None, livre, base_limits=sem, base_image="ghcr.io/o/r") == (None, [], []), "an empty image leaves the unit alone"
    t, e, _ = validate_and_render(base, img("ghcr.io/o/r"), None, livre, base_limits=sem, base_image="docker.io/x/y:1")
    assert t is None and "sem tag" in e[0], e
    t, e, _ = validate_and_render(base, img("Not An Image:1"), None, livre, base_limits=sem, base_image="")
    assert t is None and "imagem" in e[0], e
    t, e, _ = validate_and_render(base, img("ghcr.io/o/r@sha256:" + "a" * 64), None, livre, base_limits=sem, base_image="")
    assert not e and "@sha256:" in t, (e, t)
    # the network: only one that exists, and only when it differs from the unit's; the list is reset first
    net = lambda v: {**nada, "network": v}
    t, e, av = validate_and_render(base, net("casa-net.network"), None, livre, base_limits=sem, base_network="tsdproxy-net.network", redes={"casa-net.network", "tsdproxy-net.network"})
    assert not e and "Network=\nNetwork=casa-net.network" in t and av, (e, t)
    assert validate_and_render(base, net("tsdproxy-net.network"), None, livre, base_limits=sem, base_network="tsdproxy-net.network", redes={"tsdproxy-net.network"}) == (None, [], []), "the unit's own network is not a change"
    t, e, _ = validate_and_render(base, net("naoexiste.network"), None, livre, base_limits=sem, base_network="x.network", redes={"x.network"})
    assert t is None and "rede" in e[0], e
    # where the controllers are not delegated, saving a limit is refused with the reason, and a form with none is untouched
    t, e, _ = validate_and_render(base, quer(memory="512m"), None, ctx, base_limits=sem)
    assert t is None and "não delega o controlador memory" in e[0], e
    t, e, _ = validate_and_render(base, quer(cpus="1"), None, ctx, base_limits=sem)
    assert t is None and "não delega o controlador cpu" in e[0], e
    assert validate_and_render(base, nada, None, ctx, base_limits=sem) == (None, [], [])
    for ruim, trecho in ((dict(memory="lots"), "use um número"), (dict(memory="1m"), "mínimo"), (dict(memory="64g"), "mais do que este host"),
                         (dict(cpus="abc"), "use um número"), (dict(cpus="0.01"), "a partir de 0.1"), (dict(cpus="9"), "este host tem 4")):
        t, e, _ = validate_and_render(base, quer(**ruim), None, livre, base_limits=sem)
        assert t is None and any(trecho in x for x in e), (ruim, e)
    t, e, _ = validate_and_render(base, quer(), None, livre, base_limits={"memory": "1g", "cpus": ""})
    assert t is None and "edite a unit à mão" in e[0], "a limit the unit carries is not removed from here"

    assert validate_and_render(base, nada, None, ctx) == (None, [], [])
    assert validate_and_render(base, nada, "always", ctx) == (None, [], []), "same restart as the unit"

    # a change writes a reset plus the whole list, and only for the group that changed
    quer = {**nada, "ports": [{"bind": "", "host": 9100, "container": 3000, "proto": "tcp"}]}
    texto, erros, avisos = validate_and_render(base, quer, "on-failure", ctx, propria="demo")
    assert not erros and "PublishPort=\nPublishPort=9100:3000\n" in texto and "Volume=" not in texto
    assert "[Service]\nRestart=on-failure" in texto and f"# base={base_hash(base)}" in texto
    assert any("rede local" in a for a in avisos), "a new published port is said to open the LAN"
    assert merged(base, texto)[0]["ports"] == ["9100:3000"] and merged(base, texto)[1] == "on-failure"
    assert recorded_base(texto) == base_hash(base)

    # the rules for what is new
    def erro(grupo, item, **kw):
        c = Contexto("/home/u", **{"roots": ["/tmp"], "existe": ctx.existe, **kw})
        t, e, _ = validate_and_render(base, {**nada, grupo: nada[grupo] + [item]}, None, c)
        return e
    assert not erro("ports", {"bind": "", "host": 8200, "container": 80, "proto": "tcp"})
    assert erro("ports", {"bind": "", "host": 80, "container": 80, "proto": "tcp"}), "below the unprivileged floor"
    assert erro("ports", {"bind": "nao-ip", "host": 8300, "container": 80, "proto": "tcp"})
    assert erro("ports", {"bind": "", "host": 8300, "container": 99999, "proto": "tcp"})
    assert erro("ports", {"bind": "", "host": 8300, "container": 80, "proto": "tcp"}, em_uso={(8300, "tcp"): "outro"}), "another unit has it"
    assert erro("ports", {"bind": "", "host": 8300, "container": 80, "proto": "udp"}, escutando={(8300, "udp")}), "something listens"
    assert not erro("ports", {"bind": "[::1]", "host": 8300, "container": 80, "proto": "tcp"})
    assert erro("ports", {"bind": "", "host": 8085, "container": 80, "proto": "tcp"}), "a duplicate of the unit's own host port"

    vol = lambda host, cont="/x", **kw: {"host": host, "container": cont, "label": "Z", "ro": False, "extra": [], **kw}
    assert not erro("volumes", vol("/tmp/dados"))
    assert erro("volumes", vol("/etc"), ), "outside the roots"
    assert erro("volumes", vol("/tmp")), "the root itself is not inside it"
    assert erro("volumes", vol("/tmp/../etc")), "no .. to climb out"
    assert erro("volumes", vol("/tmp/a b")), "a space cuts a Volume= at the space"
    assert erro("volumes", vol("/tmp/x", "relativo"))
    assert erro("volumes", vol("/tmp/x", "/")), "not over the container's root"
    assert erro("volumes", vol("/tmp/x", extra=["U"])), "only Z, z, ro, rw"
    assert erro("volumes", vol("/tmp/x", "/a")), "the container path is already used"
    assert erro("volumes", vol("%h/.ssh")), "%h resolves, and the home is not a root"
    assert erro("volumes", vol("/run/user/1000/podman/podman.sock")), "no new path to the socket"

    assert not erro("env", {"key": "NOVA", "value": "x y $ %"})
    assert erro("env", {"key": "1X", "value": "a"}) and erro("env", {"key": "OK", "value": "a\nB=2"})
    assert erro("env", {"key": "A", "value": "outro"}), "a repeated key"
    assert not erro("caps", {"name": "NET_RAW"}) and erro("caps", {"name": "SYS_ADMIN"}), "the short list"
    assert not erro("devices", {"path": "/dev/dri"}) and erro("devices", {"path": "/dev/nao"}) and erro("devices", {"path": "/etc/passwd"})
    assert erro("ports", {"raw": "8080", "opaque": True}), "an opaque entry that is not the unit's is refused"
    t, e, _ = validate_and_render(base, nada, "sempre", ctx)
    assert e and t is None, "an unknown restart policy"

    # the base's own opaque entries survive when the group is edited
    opaca = base_of("[Container]\nPublishPort=${DNS_BIND}:53:53/udp\n")
    d2 = describe(opaca[0])
    assert d2["ports"][0].get("opaque")
    t, e, _ = validate_and_render(opaca, {**{g: [] for g, _ in GROUPS}, "ports": d2["ports"] + [{"bind": "", "host": 8400, "container": 80, "proto": "tcp"}]}, None, ctx)
    assert not e and "PublishPort=${DNS_BIND}:53:53/udp" in t and "PublishPort=8400:80" in t

    # files
    with tempfile.TemporaryDirectory() as d:
        u = Path(d) / "demo.container"
        u.write_text(DEMO)
        assert read_override(u) is None
        write_override(u, texto)
        assert read_override(u) == texto and oct(dropin_path(u).stat().st_mode)[-3:] == "600"
        assert not list(dropin_path(u).parent.glob("*.tmp"))
        remove_override(u)
        assert read_override(u) is None and not dropin_path(u).parent.exists(), "the empty folder goes too"
        write_override(u, texto)
        (dropin_path(u).parent / "10-mine.conf").write_text("[Service]\nNice=5\n")
        remove_override(u)
        assert (dropin_path(u).parent / "10-mine.conf").exists(), "somebody else's drop-in stays"

        # and the host's own generator agrees, when there is one
        ok, msgs, gerado = quadlet_check(d, u, texto)
        if ok is None:
            print("  (no quadlet generator here: the cross-check was skipped)")
        else:
            assert ok, msgs
            assert "--publish 9100:3000" in gerado and "--publish 8085:3000" not in gerado, gerado
            assert "-v %h/a:/a:Z" in gerado and "--env B=" in gerado.replace('"', ""), gerado
            ok2, msgs2, _ = quadlet_check(d, u, "[Container]\nBogusKey=1\n")
            assert ok2 is False and any("BogusKey" in m for m in msgs2), "a key Quadlet does not know is caught"
            variavel = {**nada, "env": nada["env"] + [{"key": "SP", "value": 'say "hi" $x 100%'}]}
            t3, e3, _ = validate_and_render(base, variavel, None, ctx)
            ok3, m3, g3 = quadlet_check(d, u, t3)
            assert ok3 and "SP=say\\x20\\\"hi\\\"\\x20$$x\\x20100%%" in g3, g3
    print("overrides selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
