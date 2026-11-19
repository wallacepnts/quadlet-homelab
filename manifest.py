#!/usr/bin/env python3
"""`apps/<app>/app.json`: everything one app says about itself, in one file.

The model is CasaOS's app store, where an app is a compose file with an `x-casaos` block that
carries its metadata, but in JSON of our own, beside the unit files instead of inside them:

    {
      "title": "Memos",
      "short_desc": {"en": "Quick notes.", "pt": "Notas rápidas."},   # one plain sentence, both languages
      "description": {"en": "...", "pt": "..."},      # what it is, a little longer
      "author": "usememos", "source": "https://github.com/usememos/memos",
      "website": "https://usememos.com", "docs": "https://www.usememos.com/docs",
      "architectures": ["amd64", "arm64"],            # optional: website, architectures
      "category": "Productivity",                     # one of qhui.GRUPOS
      "min_podman": "6.1",
      "requires_https": true,                         # the app breaks over plain HTTP (a vault, a service worker)
      "deprecated": "why it is discontinued",         # no install is offered
      "secrets": {"memos-token": "rand-hex 32"},      # how each Secret= is made
      "validate": {"authkey": "shell ..."},           # a value only the far end can judge
      "config": {"nginx.conf": "%h/.config/.../nginx.conf"},
      "vars": {"MEDIA_DATA_DIR": "~/data"},           # systemd variables a Volume= uses, with a default
      "ask": {"MEDIA_DATA_DIR": {"type": "path", "label": "Media folder", "hint": "…"}},   # how the install asks it
      "login": {"user": "admin", "password": "memos-token"},
      "choices": {"VERSION": {"question": "...", "options": [{"value": "11", "label": "..."}, "10"]}},
      "backup": {"mode": "stop", "exclude": ["upload/thumbs"]},
      "units": {
        "memos": {"upstream": "usememos/memos"}       # `image` only when the tag is not just {version}
      }
    }

The app's logo and screenshots are files in its folder, not fields: `icon.svg` (or `.png`, `.webp`, `.jpg`) and,
optionally, `screenshots/1.png`, `screenshots/2.png`... The store serves them itself.

`units.<unit>` also takes `login` and `choices`, for a folder of independent services.

The rest of the code reads this through `view()`, which answers the questions a ConfigParser did
(`has_section`, `items`, `get`, ...) from the JSON, so what the manifest says is validated and read in
exactly one place.

    python3 manifest.py --selftest
"""

import json
import re
import sys
from pathlib import Path

FILE = "app.json"


def path_of(folder):
    return Path(folder) / FILE


def load(folder):
    """The folder's manifest as a dict ({} when it has none, so a folder without one still loads)."""
    p = path_of(folder)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text())
    except ValueError as e:
        raise ValueError(f"{p}: not valid JSON ({e})")


WIDTH = 110          # a value that fits in this many columns stays on one line


def _inline(v):
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{json.dumps(k, ensure_ascii=False)}: {_inline(x)}" for k, x in v.items()) + " }" if v else "{}"
    if isinstance(v, list):
        return "[" + ", ".join(_inline(x) for x in v) + "]"
    return json.dumps(v, ensure_ascii=False)


def _render(v, indent, prefix_len):
    """`v` as text: on one line when it fits (like `"categories": ["finance"]`), else one entry per line."""
    linha = _inline(v)
    if not isinstance(v, (dict, list)) or not v or (prefix_len + len(linha) <= WIDTH):
        return linha
    pad, pad_in = "  " * indent, "  " * (indent + 1)
    if isinstance(v, dict):
        itens = [f"{pad_in}{json.dumps(k, ensure_ascii=False)}: " + _render(x, indent + 1, len(pad_in) + len(json.dumps(k, ensure_ascii=False)) + 2)
                 for k, x in v.items()]
        return "{\n" + ",\n".join(itens) + f"\n{pad}}}"
    itens = [pad_in + _render(x, indent + 1, len(pad_in)) for x in v]
    return "[\n" + ",\n".join(itens) + f"\n{pad}]"


def dump(data):
    """The canonical text of a manifest, the way Runtipi writes its config.json: one key per line, keys in the
    order the spec lists them, a short object or list kept on its line and a long one broken into one entry per line."""
    d = ordered(data)
    if not d:
        return "{}\n"
    linhas = [f"  {json.dumps(k, ensure_ascii=False)}: " + _render(v, 1, 2 + len(json.dumps(k, ensure_ascii=False)) + 2) for k, v in d.items()]
    return "{\n" + ",\n".join(linhas) + "\n}\n"


KEY_ORDER = ["$schema", "title", "short_desc", "description", "author", "website", "source", "docs", "demo", "video", "license", "architectures", "category",
             "min_podman", "requires_https", "no_gui", "deprecated", "secrets", "validate", "config", "vars", "ask",
             "login", "choices", "options", "widgets", "icon", "backup", "units", "instance"]


def ordered(data):
    saida = {k: data[k] for k in KEY_ORDER if k in data}
    saida.update({k: v for k, v in data.items() if k not in saida})
    return saida


# -- the ConfigParser-shaped view -----------------------------------------------------------

class View:
    """What `configparser.ConfigParser` answered, from a manifest: sections, options, items, get.

    The names of the sections are the ones install.ini used (`secrets`, `upstream`, `image`, `store`,
    `backup`, `config`, `vars`, `validate`, `login`, `login.<unit>`, `choices`, `choices.<unit>`), so the
    code that asked those questions did not have to change when the file did."""

    def __init__(self, data, folder=None):
        self.data = data or {}
        self.folder = Path(folder) if folder else None
        self._s = self._build(self.data)

    @staticmethod
    def _lines(valor):
        return "\n".join(valor) if isinstance(valor, list) else valor

    def _build(self, d):
        s = {}

        def pairs(secao, mapa):
            if mapa:
                s.setdefault(secao, {}).update(dict(mapa))

        pairs("secrets", d.get("secrets"))
        pairs("validate", d.get("validate"))
        pairs("config", d.get("config"))
        pairs("vars", d.get("vars"))
        login = d.get("login")
        if login:
            s["login"] = {k: v for k, v in login.items()}
        upstream, image = {}, {}
        for unit, u in (d.get("units") or {}).items():
            if "upstream" in u:
                upstream[unit] = u["upstream"]
            if "image" in u:
                image[unit] = u["image"]
            if u.get("login"):
                s[f"login.{unit}"] = {k: v for k, v in u["login"].items()}
            if u.get("choices"):
                s[f"choices.{unit}"] = {k: self._choice(v) for k, v in u["choices"].items()}
        # A unit whose Image= has no tag follows a GitHub release and needs a template; `{version}` is the
        # one nearly all of them use, so it is implied: only a different shape is written down.
        if self.folder and self.folder.is_dir():
            for c in sorted(self.folder.glob("*.container")):
                if c.stem in image:
                    continue
                m = re.search(r"(?m)^Image=(\S+)$", c.read_text())
                if not m or "@" in m.group(1) or ":" in m.group(1).rpartition("/")[2]:
                    continue                                    # pinned here: a tag or a digest
                fonte = str(upstream.get(c.stem, ""))
                if fonte == "-" or fonte.startswith(("registry", "compose:")):
                    continue                                    # not a GitHub release: no template can fill it
                image[c.stem] = "{version}"
        if upstream:
            s["upstream"] = upstream
        if image:
            s["image"] = image
        if d.get("choices"):
            s["choices"] = {k: self._choice(v) for k, v in d["choices"].items()}
        loja = {}
        if d.get("category"):
            loja["group"] = d["category"]
        for chave, campo in (("docs", "docs"), ("repo", "source")):
            if d.get(campo):
                loja[chave] = d[campo]
        if d.get("min_podman"):
            loja["min_podman"] = d["min_podman"]
        if d.get("requires_https"):
            loja["requires_https"] = "true"
        if d.get("deprecated"):
            loja["deprecated"] = d["deprecated"]
        if loja:
            s["store"] = loja
        backup = d.get("backup")
        if backup:
            s["backup"] = {}
            if backup.get("mode"):
                s["backup"]["mode"] = backup["mode"]
            if backup.get("exclude"):
                s["backup"]["exclude"] = "\n" + "\n".join(backup["exclude"])
        return s

    @staticmethod
    def _choice(c):
        """`{"question": q, "options": [...]}` as the block the installer parses: the question, then one
        `value: label` line per option. An option is `{"value", "label"}`, or just the value as a string."""
        def linha(o):
            if isinstance(o, str):
                return o
            return f"{o['value']}: {o['label']}" if o.get("label") else o["value"]
        return "\n".join([c["question"]] + [linha(o) for o in c["options"]])

    # the ConfigParser surface the code used
    def sections(self):
        return list(self._s)

    def has_section(self, s):
        return s in self._s

    def has_option(self, s, k):
        return k in self._s.get(s, {})

    def options(self, s):
        return list(self._s[s])

    def items(self, s):
        if s not in self._s:
            raise KeyError(s)
        return list(self._s[s].items())

    def get(self, s, k, fallback=None, **_):
        return self._s.get(s, {}).get(k, fallback)

    def __getitem__(self, s):
        return self._s[s]

    def __contains__(self, s):
        return s in self._s


def view(folder):
    return View(load(folder), folder)


# -- the files beside it: logo and screenshots ----------------------------------------------------

ICON_SUFFIXES = (".svg", ".png", ".webp", ".jpg")
SHOT_SUFFIXES = (".png", ".webp", ".jpg", ".jpeg", ".gif")
TAGLINE_MAX = 70
ICON_MAX, SHOT_MAX, SHOT_COUNT = 512 * 1024, 1024 * 1024, 6


def icon_file(folder):
    """The name of the app's logo (`icon.svg`, `icon.png`...) or None."""
    for suf in ICON_SUFFIXES:
        if (Path(folder) / f"icon{suf}").is_file():
            return f"icon{suf}"
    return None


def screenshot_files(folder):
    """The names of the files in `screenshots/`, in order (1.png, 2.png, ...), images only."""
    d = Path(folder) / "screenshots"
    if not d.is_dir():
        return []
    return sorted((f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() in SHOT_SUFFIXES),
                  key=lambda n: (len(n.split(".")[0]), n))


def assets_problems(folder):
    """What is wrong with the logo and screenshots of a folder, as a list."""
    folder, erros = Path(folder), []
    icon = icon_file(folder)
    if icon is None:
        erros.append("has no logo: put icon.svg (or .png, .webp, .jpg) in the folder")
    elif (folder / icon).stat().st_size > ICON_MAX:
        erros.append(f"{icon} is over {ICON_MAX // 1024} KB")
    shots = screenshot_files(folder)
    if len(shots) > SHOT_COUNT:
        erros.append(f"screenshots/ has {len(shots)} images, at most {SHOT_COUNT}")
    for n in shots:
        if (folder / "screenshots" / n).stat().st_size > SHOT_MAX:
            erros.append(f"screenshots/{n} is over {SHOT_MAX // 1024} KB")
    d = folder / "screenshots"
    if d.is_dir():
        for f in d.iterdir():
            if f.name not in shots:
                erros.append(f"screenshots/{f.name} is not an image the store can show ({', '.join(SHOT_SUFFIXES)})")
    return erros


NOTES_MAX = 2500            # characters: a note is what to do first, not a manual (that goes in docs/)


def notes_file(folder, lang):
    return Path(folder) / f"notes.{lang}.md"


def notes(folder):
    """The app's notes, {"en": markdown|None, "pt": markdown|None}: what to do at the first run and what is odd about it.

    They live beside app.json in `notes.en.md` and `notes.pt.md`, written only for an app that really needs one."""
    return {lang: (notes_file(folder, lang).read_text().strip() or None) if notes_file(folder, lang).is_file() else None
            for lang in ("en", "pt")}


def notes_problems(folder):
    """Both languages or neither, and short enough to be read."""
    erros, n = [], notes(folder)
    if bool(n["en"]) != bool(n["pt"]):
        erros.append("notes.en.md and notes.pt.md go together: write the one that is missing")
    for lang, texto in n.items():
        if texto and len(texto) > NOTES_MAX:
            erros.append(f"notes.{lang}.md has {len(texto)} characters, at most {NOTES_MAX}: the rest belongs in docs/")
    return erros


# -- install options ----------------------------------------------------------------------------

OPTION_KEY = re.compile(r"[a-z][a-z0-9_]{0,30}")
VALUE_KEY = re.compile(r"[a-z0-9][a-z0-9._-]{0,30}")


ICON_TONES = ("light", "color", "dark", "full")


def option_problems(data, folder=None):
    """What is wrong with `options`, as a list.

    `options.<key>` is a choice the developer offers at the first install (a database, say):
    `{"question": "...", "default": "<value>", "values": {"<value>": {"label": "...", "units": [...],
    "env": {"VAR": "x"}, "secrets": ["name", "other:VAR"]}}}`. A value switches on the optional units it names, adds
    the variables to the `.env` and brings the secrets it needs. With `folder`, a named unit has to be a
    `.container` there; a named secret has to be one `secrets` makes."""
    ops = data.get("options")
    if ops is None:
        return []
    if not isinstance(ops, dict):
        return ['"options" must be an object']
    erros = []
    feitos = set(data.get("secrets") or {}) if isinstance(data.get("secrets"), dict) else set()
    for chave, o in ops.items():
        onde = f'options.{chave}'
        if not OPTION_KEY.fullmatch(str(chave)):
            erros.append(f'{onde}: the key is lowercase letters, digits and _')
        if not isinstance(o, dict):
            erros.append(f"{onde} must be an object")
            continue
        for k in set(o) - {"question", "default", "values"}:
            erros.append(f"{onde}: unknown key {k!r}")
        if not isinstance(o.get("question"), str) or not o["question"].strip():
            erros.append(f'{onde}: "question" is required')
        vals = o.get("values")
        if not isinstance(vals, dict) or len(vals) < 2:
            erros.append(f'{onde}: "values" needs at least two values (one is no choice)')
            continue
        if o.get("default") not in vals:
            erros.append(f'{onde}: "default" must be one of the values: {", ".join(vals)}')
        for nome, v in vals.items():
            ov = f"{onde}.{nome}"
            if not VALUE_KEY.fullmatch(str(nome)):
                erros.append(f"{ov}: the value is lowercase letters, digits, . _ -")
            if not isinstance(v, dict):
                erros.append(f"{ov} must be an object")
                continue
            for k in set(v) - {"label", "units", "env", "secrets"}:
                erros.append(f"{ov}: unknown key {k!r}")
            if not isinstance(v.get("label"), str) or not v["label"].strip():
                erros.append(f'{ov}: "label" is required')
            for k in ("units", "secrets"):
                if k in v and not (isinstance(v[k], list) and all(isinstance(x, str) and x for x in v[k])):
                    erros.append(f'{ov}: "{k}" is a list of names')
            if "env" in v and not (isinstance(v["env"], dict) and all(isinstance(a, str) and isinstance(b, str)
                                                                      and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", a)
                                                                      for a, b in v["env"].items())):
                erros.append(f'{ov}: "env" is {{"VARIABLE": "value"}}')
            if folder is not None:
                for u in v.get("units", []) if isinstance(v.get("units"), list) else []:
                    if not (Path(folder) / f"{u}.container").is_file():
                        erros.append(f"{ov}: unit {u!r} is not a .container in the folder")
            for sec in v.get("secrets", []) if isinstance(v.get("secrets"), list) else []:
                if sec.partition(":")[0] not in feitos:
                    erros.append(f'{ov}: secret {sec!r} has no recipe in "secrets"')
    return erros


def option_units(data):
    """The units some value of some option names: optional, so they are only on when a chosen value says so."""
    return {u for o in (data.get("options") or {}).values() for v in o.get("values", {}).values() for u in v.get("units", [])}


def chosen_options(data, chosen=None):
    """{option: value} with the default where nothing was chosen (an unknown choice is ignored)."""
    saida = {}
    for chave, o in (data.get("options") or {}).items():
        v = (chosen or {}).get(chave)
        saida[chave] = v if v in o["values"] else o["default"]
    return saida


def active_units(data, all_units, chosen=None):
    """The units to install: every one no value names, plus those the chosen values name."""
    ligadas = {u for chave, nome in chosen_options(data, chosen).items()
               for u in data["options"][chave]["values"][nome].get("units", [])}
    return [u for u in all_units if u not in option_units(data) or u in ligadas]


def option_env(data, chosen=None):
    """The variables the chosen values add to the `.env`."""
    return {k: v for chave, nome in chosen_options(data, chosen).items()
            for k, v in data["options"][chave]["values"][nome].get("env", {}).items()}


def option_secrets(data, chosen=None):
    """The extra secrets the chosen values need, in order, without repeats."""
    return list(dict.fromkeys(s.partition(":")[0] for chave, nome in chosen_options(data, chosen).items()
                              for s in data["options"][chave]["values"][nome].get("secrets", [])))


def option_secret_env(data, chosen=None):
    """[(secret, VARIABLE)]: the chosen values' `"secret:VARIABLE"` entries, which hand a secret to the
    main unit as an environment variable. A bare `"secret"` is only created (another unit uses it)."""
    return [(s.partition(":")[0], s.partition(":")[2]) for chave, nome in chosen_options(data, chosen).items()
            for s in data["options"][chave]["values"][nome].get("secrets", []) if ":" in s]


# -- validation -------------------------------------------------------------------------------

ASK_TYPES = ("text", "password", "email", "number", "url", "path")
ASK_FIELDS = {"type", "label", "hint", "placeholder", "min", "max", "regex", "pattern_error", "required"}
ASK_TEXTS = ("label", "hint", "placeholder", "pattern_error")


def say(v, lang="en"):
    """A text that is a string or an {en, pt} pair, in `lang` (English when it has no such one)."""
    return (v.get(lang) or v.get("en") or "") if isinstance(v, dict) else (v or "")


def ask_problems(ask, manuais, variaveis):
    """What is wrong with `ask`: the form the install shows for a secret typed by hand or a ${VAR}, one line each."""
    if not isinstance(ask, dict) or not ask:
        return ['"ask" is an object, one entry per manual secret or `vars` name']
    erros = []
    for nome, a in ask.items():
        if nome not in manuais and nome not in variaveis:
            erros.append(f'"ask" {nome!r} is neither a `manual` secret nor a `vars` name')
        if not isinstance(a, dict) or set(a) - ASK_FIELDS:
            erros.append(f'"ask" {nome!r} takes only: {", ".join(sorted(ASK_FIELDS))}')
            continue
        if a.get("type", "text") not in ASK_TYPES:
            erros.append(f'"ask" {nome!r}: "type" is one of {", ".join(ASK_TYPES)}')
        for k in ASK_TEXTS:
            v = a.get(k)
            if v is not None and not (isinstance(v, str) or (isinstance(v, dict) and set(v) == {"en", "pt"}
                                                              and all(isinstance(x, str) for x in v.values()))):
                erros.append(f'"ask" {nome!r}: "{k}" is a text or an {{"en", "pt"}} pair')
        for k in ("min", "max"):
            if k in a and (isinstance(a[k], bool) or not isinstance(a[k], int)):
                erros.append(f'"ask" {nome!r}: "{k}" is a whole number')
        if "min" in a and "max" in a and isinstance(a["min"], int) and isinstance(a["max"], int) and a["min"] > a["max"]:
            erros.append(f'"ask" {nome!r}: "min" is above "max"')
        if "required" in a and not isinstance(a["required"], bool):
            erros.append(f'"ask" {nome!r}: "required" is true or false')
        if "regex" in a:
            try:
                re.compile(a["regex"])
            except (re.error, TypeError):
                erros.append(f'"ask" {nome!r}: "regex" does not compile')
    return erros


def check_value(a, valor, lang="en"):
    """Why `valor` does not fit the `ask` entry `a`, as a message in `lang`; None when it does."""
    pt = lang == "pt"
    tipo = a.get("type", "text")
    if not valor:
        return (("obrigatório" if pt else "required") if a.get("required") else None)
    n = len(valor)
    if tipo == "number":
        try:
            n = int(valor)
        except ValueError:
            return "precisa ser um número" if pt else "must be a number"
        if "min" in a and n < a["min"]:
            return f"no mínimo {a['min']}" if pt else f"at least {a['min']}"
        if "max" in a and n > a["max"]:
            return f"no máximo {a['max']}" if pt else f"at most {a['max']}"
    else:
        if "min" in a and n < a["min"]:
            return f"no mínimo {a['min']} caracteres" if pt else f"at least {a['min']} characters"
        if "max" in a and n > a["max"]:
            return f"no máximo {a['max']} caracteres" if pt else f"at most {a['max']} characters"
    if tipo == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        return "e-mail inválido" if pt else "not an email address"
    if tipo == "url" and not re.match(r"https?://\S+$", valor):
        return "use um endereço http:// ou https://" if pt else "use an http:// or https:// address"
    if a.get("regex") and not re.fullmatch(a["regex"], valor):
        return say(a.get("pattern_error"), lang) or ("formato inválido" if pt else "wrong format")
    return None


SCHEMA_REF = "../app-schema.json"        # apps/app-schema.json, seen from apps/<app>/app.json


def schema(grupos):
    """The JSON Schema of a manifest, for the editor: completion and a red squiggle while the file is written.

    Built from the same lists `problems` uses, so it cannot drift far; `check.py` fails when the file on disk
    differs from this, and `check.py --schema` rewrites it. It states the shape, `problems` still states the rules."""
    texto = {"type": "string", "minLength": 1}
    par = {"type": "object", "properties": {"en": texto, "pt": texto}, "required": ["en", "pt"], "additionalProperties": False}
    mapa = lambda v: {"type": "object", "additionalProperties": v}            # noqa: E731
    ask_texto = {"oneOf": [{"type": "string"}, par]}
    campo = {"type": "object", "additionalProperties": False, "properties": {
        "type": {"enum": list(ASK_TYPES)}, "label": ask_texto, "hint": ask_texto, "placeholder": ask_texto,
        "pattern_error": ask_texto, "min": {"type": "integer"}, "max": {"type": "integer"},
        "regex": {"type": "string"}, "required": {"type": "boolean"}}}
    props = {
        "$schema": {"type": "string"},
        "title": texto, "short_desc": par, "description": par, "author": texto,
        "website": {"type": "string", "format": "uri"}, "source": {"type": "string", "format": "uri"},
        "docs": {"type": "string", "format": "uri"}, "demo": {"type": "string", "format": "uri"},
        "video": {"type": "string", "format": "uri"}, "license": {"type": "string", "minLength": 1, "maxLength": 40},
        "architectures": {"type": "array", "items": texto},
        "category": {"enum": list(grupos)}, "min_podman": {"type": "string"},
        "requires_https": {"type": "boolean"}, "no_gui": {"const": True}, "deprecated": par,
        "secrets": mapa(texto), "validate": mapa(texto), "config": mapa(texto),
        "vars": mapa(texto), "ask": mapa(campo), "login": {"type": "object"}, "choices": {"type": "object"},
        "options": {"type": "object"}, "widgets": {"type": "array", "items": {"type": "object", "required": ["type"]}},
        "icon": {"type": "object", "additionalProperties": False, "properties": {
            "bg": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}, "fit": {"type": "number"}, "tone": {"enum": list(ICON_TONES)}}},
        "backup": {"type": "object"}, "units": mapa({"type": "object"}), "instance": {"type": "object"},
    }
    assert set(props) == set(KEY_ORDER), set(props) ^ set(KEY_ORDER)
    return {"$schema": "http://json-schema.org/draft-07/schema#", "title": "quadlet-homelab app manifest",
            "type": "object", "required": ["title", "short_desc", "description"], "additionalProperties": False,
            "properties": {k: props[k] for k in KEY_ORDER}}


def schema_text(grupos):
    return json.dumps(schema(grupos), ensure_ascii=False, indent=2) + "\n"


def problems(data, grupos, folder=None):
    """What is wrong with a manifest, as a list of messages; empty when it holds.

    With `folder` the files beside it are checked too (the logo has to be there)."""
    erros = []
    if not data.get("title"):
        erros.append('"title" is required')
    if data.get("category") and data["category"] not in grupos:     # optional: infrastructure has none
        erros.append(f'"category" {data["category"]!r} is not one of: {", ".join(grupos)}')
    for k in ("short_desc", "description"):
        v = data.get(k)
        if not isinstance(v, dict) or set(v) != {"en", "pt"} or not all(isinstance(x, str) and x.strip() for x in v.values()):
            erros.append(f'"{k}" is required: an object with a non-empty "en" and "pt"')
    for lang, tag in (data.get("short_desc") or {}).items() if isinstance(data.get("short_desc"), dict) else ():
        if isinstance(tag, str) and (len(tag) > TAGLINE_MAX or "\n" in tag or " — " in tag or "(" in tag):
            erros.append(f'"short_desc.{lang}" must be one short, plain sentence: up to {TAGLINE_MAX} characters, no dash or parenthesis')
    for k in ("author", "website", "source", "docs", "demo", "video"):
        if k in data and not isinstance(data[k], str):
            erros.append(f'"{k}" must be a string')
        elif k in ("website", "source", "docs", "demo", "video") and data.get(k) and not re.fullmatch(r"https://[A-Za-z0-9.-]+(/\S*)?", data[k]):
            erros.append(f'"{k}" must be a plain https:// URL')
    lic = data.get("license")
    if lic is not None and (not isinstance(lic, str) or not lic.strip() or len(lic) > 40 or "\n" in lic):
        erros.append('"license" must be a short text: an SPDX identifier (MIT, AGPL-3.0, Apache-2.0…) or the licence\'s name')
    arq = data.get("architectures")
    if arq is not None and (not isinstance(arq, list) or not arq or not set(arq) <= {"amd64", "arm64", "arm", "riscv64", "386", "ppc64le", "s390x"}):
        erros.append('"architectures" must be a list of: amd64, arm64, arm, riscv64, 386, ppc64le, s390x')
    if "requires_https" in data and data["requires_https"] is not True:
        erros.append('"requires_https" is `true` or left out')
    if "deprecated" in data and not isinstance(data["deprecated"], str):
        erros.append('"deprecated" must be a string')
    for k in ("secrets", "validate", "config", "vars"):
        if k in data and not isinstance(data[k], dict):
            erros.append(f'"{k}" must be an object')
    if "units" in data and not isinstance(data["units"], dict):
        erros.append('"units" must be an object')
    if "no_gui" in data and data["no_gui"] is not True:
        erros.append('"no_gui" is true (leave it out for an app with a web interface)')
    if "ask" in data:
        sec = data.get("secrets") if isinstance(data.get("secrets"), dict) else {}
        manuais = {k for k, v in sec.items() if isinstance(v, str) and v.startswith("manual")}
        erros.extend(ask_problems(data["ask"], manuais, set(data.get("vars") if isinstance(data.get("vars"), dict) else {})))
    ws = data.get("widgets")
    if ws is not None and (not isinstance(ws, list) or not ws or not all(
            isinstance(w, dict) and isinstance(w.get("type"), str) and set(w) <= {"type", "unit"}
            and (w.get("unit") is None or isinstance(w["unit"], str)) for w in ws)):
        erros.append('"widgets" is a list of {"type": "...", "unit": "..."} (unit only in a folder of several)')
    ic = data.get("icon")
    if ic is not None:
        if not isinstance(ic, dict) or not ic or set(ic) - {"bg", "fit", "tone"}:
            erros.append('"icon" is {"bg": "#rrggbb", "fit": 1.2, "tone": "light|color|dark|full"}, each optional')
        else:
            if "bg" in ic and not (isinstance(ic["bg"], str) and re.fullmatch(r"#[0-9a-fA-F]{6}", ic["bg"])):
                erros.append('"icon.bg" is a #rrggbb colour')
            if "fit" in ic and not (isinstance(ic["fit"], (int, float)) and not isinstance(ic["fit"], bool) and 0.8 <= ic["fit"] <= 1.4):
                erros.append('"icon.fit" is a number from 0.8 to 1.4')
            if "tone" in ic and ic["tone"] not in ICON_TONES:
                erros.append(f'"icon.tone" is one of: {", ".join(ICON_TONES)}')
    if "instance" in data:
        erros.append('"instance" is written by qh into the folder of an instance, never by hand')
    erros += option_problems(data, folder)
    if "$schema" in data and data["$schema"] != SCHEMA_REF:
        erros.append(f'"$schema" is {SCHEMA_REF!r}')
    desconhecidas = set(data) - set(KEY_ORDER)
    if desconhecidas:
        erros.append(f"unknown key(s): {', '.join(sorted(desconhecidas))}")
    if folder is not None:
        erros += assets_problems(folder) + notes_problems(folder)
    return erros


# -- the services table in the READMEs ---------------------------------------------------------

TABLE_BEGIN = "<!-- services:begin (generated from apps/*/app.json: python3 check.py --readme) -->"
TABLE_END = "<!-- services:end -->"
HEAD = {"en": ("Logo", "Application", "Description"), "pt": ("Logo", "Aplicativo", "Descrição")}   # the line itself is English in both


def services_table(entries, lang):
    """The markdown table of every app: logo, name linked to its folder, one-line description.

    `entries` is [(folder name, manifest, logo file name)]; the logo is the file beside the manifest."""
    prefixo = "./apps/" if lang == "en" else "../../apps/"
    cab = HEAD[lang]
    linhas = [f"| {cab[0]} | {cab[1]} | {cab[2]} |", "| --- | --- | --- |"]
    for nome, d, icon in sorted(entries, key=lambda x: x[1]["title"].casefold()):
        linhas.append(f'| <img src="{prefixo}{nome}/{icon}" width="48" height="48" alt=""> | '
                      f'[{d["title"]}]({prefixo}{nome}) | {d["short_desc"][lang]} |')
    return "\n".join(linhas)


def splice(readme_text, tabela):
    """The README with the table between its markers replaced (the markers are added on first use)."""
    if TABLE_BEGIN in readme_text and TABLE_END in readme_text:
        a = readme_text.index(TABLE_BEGIN) + len(TABLE_BEGIN)
        b = readme_text.index(TABLE_END)
        return readme_text[:a] + "\n\n" + tabela + "\n\n" + readme_text[b:]
    return None


def selftest():
    import tempfile
    d = {"title": "X", "category": "Tools", "short_desc": {"en": "a one-liner", "pt": "uma linha"},
         "description": {"en": "long", "pt": "longa"}, "author": "o", "source": "https://github.com/o/r",
         "docs": "https://d.example", "architectures": ["amd64"], "min_podman": "6.1", "requires_https": True, "deprecated": "gone",
         "secrets": {"s1": "rand-hex 8", "s2": "shell x"},
         "config": {"c.conf": "%h/c"}, "vars": {"V": "~/v"}, "validate": {"s1": "shell y"},
         "login": {"user": "u", "password": "s1"},
         "choices": {"VERSION": {"question": "Which?", "options": [{"value": "1", "label": "One"}, "2"]}},
         "backup": {"mode": "stop", "exclude": ["a/b", "c"]},
         "units": {"x": {"upstream": "o/r", "image": "v{version}"},
                   "y": {"upstream": "-", "login": {"user": "z", "password": "s2"},
                         "choices": {"K": {"question": "Q", "options": [{"value": "a", "label": "A"}]}}}}}
    v = View(d)
    assert v.get("secrets", "s2") == "shell x" and v.get("secrets", "s1") == "rand-hex 8"
    assert v.items("upstream") == [("x", "o/r"), ("y", "-")] and v.items("image") == [("x", "v{version}")]
    assert v.get("store", "group") == "Tools" and v.get("store", "docs") == "https://d.example" and v.get("store", "repo") == "https://github.com/o/r" and v.get("store", "deprecated") == "gone"
    assert not v.has_option("store", "screenshots") and not v.has_option("store", "works_with")
    assert v.get("backup", "exclude") == "\na/b\nc" and v.get("backup", "mode") == "stop"
    assert v.get("choices", "VERSION") == "Which?\n1: One\n2", "an option may be just its value"
    assert v.get("choices.y", "K") == "Q\na: A"
    assert v.get("login.y", "user") == "z" and v.get("login", "password") == "s1"
    assert v.has_section("vars") and not v.has_section("nope") and v.get("nope", "k", fallback="f") == "f"
    assert set(v.sections()) >= {"secrets", "upstream", "image", "store", "backup", "config", "vars", "validate",
                                 "login", "login.y", "choices", "choices.y"}
    assert dump(d).startswith('{\n  "title": "X"')
    assert problems(d, ("Tools",)) == [] and problems({**d, "spec": 2}, ("Tools",)), "no version field: `spec` is a typo now"
    sd = lambda en, pt="x": {**d, "short_desc": {"en": en, "pt": pt}}
    assert problems(sd("x" * 71), ("Tools",)) and problems(sd("A tool (with a caveat)"), ("Tools",)) and problems(sd("a", "p (q)"), ("Tools",))
    assert problems(sd(""), ("Tools",)) and problems({**d, "short_desc": "plain"}, ("Tools",)) and problems({**d, "description": {"en": "a"}}, ("Tools",))
    assert problems({**d, "architectures": ["x86"]}, ("Tools",)) and problems({**d, "source": "http://x"}, ("Tools",))
    assert problems({**d, "tagline": "old"}, ("Tools",)), "tagline became short_desc"
    assert v.get("store", "requires_https") == "true" and problems({**d, "requires_https": False}, ("Tools",))
    assert problems({**d, "category": "Nope"}, ("Tools",)) and problems({**d, "notes": "x"}, ("Tools",))
    opt = {"database": {"question": "Database?", "default": "sqlite", "values": {
        "sqlite": {"label": "SQLite"},
        "postgres": {"label": "PostgreSQL", "units": ["x-pg"], "env": {"DB": "pg"}, "secrets": ["s1"]}}}}
    dd = {**d, "options": opt}
    assert problems(dd, ("Tools",)) == [] and option_units(dd) == {"x-pg"}
    assert chosen_options(dd) == {"database": "sqlite"} and chosen_options(dd, {"database": "nope"}) == {"database": "sqlite"}
    assert active_units(dd, ["x", "x-pg"]) == ["x"] and active_units(dd, ["x", "x-pg"], {"database": "postgres"}) == ["x", "x-pg"]
    assert option_env(dd) == {} and option_env(dd, {"database": "postgres"}) == {"DB": "pg"}
    assert option_secrets(dd, {"database": "postgres"}) == ["s1"] and option_secrets(dd) == []
    dm = {**d, "options": {"database": {**opt["database"], "values": {**opt["database"]["values"],
          "postgres": {"label": "P", "secrets": ["s1:DB_PASS"]}}}}}
    assert problems(dm, ("Tools",)) == [] and option_secret_env(dm, {"database": "postgres"}) == [("s1", "DB_PASS")]
    assert option_secrets(dm, {"database": "postgres"}) == ["s1"] and option_secret_env(dm) == []
    bad = lambda o: problems({**d, "options": o}, ("Tools",))
    assert bad({"Database": opt["database"]}) and bad({"database": {**opt["database"], "default": "mysql"}})
    assert bad({"database": {**opt["database"], "values": {"a": {"label": "A"}}}}), "one value is no choice"
    assert bad({"database": {**opt["database"], "values": {"a": {"label": "A"}, "b": {}}}}), "a label is required"
    assert bad({"database": {**opt["database"], "question": ""}}) and bad({"database": {**opt["database"], "x": 1}})
    assert bad({"database": {**opt["database"], "values": {"a": {"label": "A"}, "b": {"label": "B", "secrets": ["nope"]}}}})
    assert bad({"database": {**opt["database"], "values": {"a": {"label": "A"}, "b": {"label": "B", "env": {"1x": "y"}}}}})
    assert problems({**d, "widgets": [{"type": "immich"}, {"type": "sonarr", "unit": "x"}]}, ("Tools",)) == []
    assert problems({**d, "widgets": [{"kind": "immich"}]}, ("Tools",)) and problems({**d, "widgets": []}, ("Tools",))
    assert problems({**d, "icon": {"bg": "#12352a", "fit": 1.2, "tone": "dark"}}, ("Tools",)) == []
    assert problems({**d, "icon": {"bg": "green"}}, ("Tools",)) and problems({**d, "icon": {"fit": 3}}, ("Tools",)) and problems({**d, "icon": {"tone": "neon"}}, ("Tools",)) and problems({**d, "icon": {}}, ("Tools",))
    assert problems({**d, "wat": 1}, ("Tools",)), "an unknown key is a typo"
    assert not problems({**d, "no_gui": True}, ("Tools",)) and problems({**d, "no_gui": False}, ("Tools",)), "no_gui is true or absent"
    assert problems({**d, "icon": "https://x/y.svg"}, ("Tools",)), "the logo is a file now, not a field"
    assert problems({**d, "license": "MIT"}, ("Tools",)), "no licence field: the project's own repository says"
    tab = services_table([("x", d, "icon.svg"), ("a", {**d, "title": "a-first", "short_desc": {"en": "p", "pt": "q"}}, "icon.png")], "pt")
    assert tab.splitlines()[0] == "| Logo | Aplicativo | Descrição |", tab
    assert '<img src="../../apps/a/icon.png"' in tab.splitlines()[2] and "[a-first](../../apps/a) | q |" in tab.splitlines()[2], tab
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        sub = pasta / "opt"
        sub.mkdir()
        assert any("x-pg" in e for e in option_problems(dd, sub)), "a named unit has to exist in the folder"
        (sub / "x-pg.container").write_text("[Container]\nImage=x\n")
        assert option_problems(dd, sub) == []
        # an Image= with no tag implies the `{version}` template; a different shape, a tag, a digest or a
        # source that is not a GitHub release does not
        (pasta / "app.container").write_text("[Container]\nImage=docker.io/o/app\n")
        (pasta / "app-tagged.container").write_text("[Container]\nImage=docker.io/o/app:1.0\n")
        (pasta / "app-db.container").write_text("[Container]\nImage=docker.io/o/db\n")
        (pasta / "app-odd.container").write_text("[Container]\nImage=docker.io/o/odd\n")
        (pasta / "app-dig.container").write_text("[Container]\nImage=docker.io/o/dig@sha256:ab\n")
        dados = {"units": {"app-db": {"upstream": "-"}, "app-odd": {"image": "v{version}"}}}
        vv = View(dados, pasta)
        assert dict(vv.items("image")) == {"app": "{version}", "app-odd": "v{version}"}, vv.items("image")
        assert View(dados).has_section("image") and dict(View(dados).items("image")) == {"app-odd": "v{version}"}, "no folder, no implied template"
        for f in pasta.glob("*.container"):
            f.unlink()
        assert icon_file(pasta) is None and "has no logo" in assets_problems(pasta)[0]
        (pasta / "icon.svg").write_text("<svg/>")
        assert icon_file(pasta) == "icon.svg" and assets_problems(pasta) == []
        (pasta / "screenshots").mkdir()
        for n in ("10.png", "2.png", "1.webp"):
            (pasta / "screenshots" / n).write_bytes(b"x")
        assert screenshot_files(pasta) == ["1.webp", "2.png", "10.png"], "numeric order, not text order"
        (pasta / "screenshots" / "notes.txt").write_text("x")
        assert any("not an image" in e for e in assets_problems(pasta))
        (pasta / "screenshots" / "notes.txt").unlink()
        for i in range(4):
            (pasta / "screenshots" / f"{i + 3}.png").write_bytes(b"x")
        assert any("at most 6" in e for e in assets_problems(pasta))
    assert splice("a\n" + TABLE_BEGIN + "\nold\n" + TABLE_END + "\nz", "T").count("T") == 1
    assert splice("no markers", "T") is None
    # notes: both languages or neither, short enough to read
    with tempfile.TemporaryDirectory() as tmp:
        assert notes(tmp) == {"en": None, "pt": None} and not notes_problems(tmp)
        notes_file(tmp, "en").write_text("Do this.\n")
        assert notes(tmp)["en"] == "Do this." and notes_problems(tmp), "one language alone is refused"
        notes_file(tmp, "pt").write_text("x" * (NOTES_MAX + 1))
        assert any("at most" in e for e in notes_problems(tmp)), "too long"
        notes_file(tmp, "pt").write_text("Faça isto.\n")
        assert not notes_problems(tmp)
    # ask: the form of a manual secret or a ${VAR}
    base = {"title": "x", "short_desc": {"en": "a", "pt": "a"}, "description": {"en": "a", "pt": "a"},
            "secrets": {"k": "manual paste it", "r": "rand-hex 8"}, "vars": {"V": "~/v"}}
    ok = {"k": {"type": "password", "label": {"en": "Key", "pt": "Chave"}, "min": 12, "required": True}, "V": {"type": "path"}}
    assert not [e for e in problems({**base, "ask": ok}, ("Tools",)) if "ask" in e]
    for ruim in ({"r": {}}, {"k": {"type": "nope"}}, {"k": {"min": "x"}}, {"k": {"regex": "("}}, {"k": {"zzz": 1}},
                 {"k": {"label": {"en": "only"}}}, {"k": {"min": 9, "max": 3}}, {"nope": {}}, []):
        assert [e for e in problems({**base, "ask": ruim}, ("Tools",)) if "ask" in e], ruim
    chave = {"type": "password", "min": 12, "max": 20, "required": True}
    assert check_value(chave, "") == "required" and check_value(chave, "short") == "at least 12 characters"
    assert check_value(chave, "x" * 12) is None and check_value(chave, "x" * 21, "pt") == "no máximo 20 caracteres"
    assert check_value({"type": "number", "min": 1, "max": 10}, "11") == "at most 10"
    assert check_value({"type": "number"}, "a") == "must be a number" and check_value({"type": "email"}, "a@b.co") is None
    assert check_value({"type": "url"}, "ftp://x") and check_value({"type": "url"}, "https://x.y") is None
    assert check_value({"regex": "[a-z]+", "pattern_error": {"en": "letters", "pt": "letras"}}, "A1", "pt") == "letras"
    assert check_value({}, "") is None, "optional and empty is fine"
    print("manifest selftest: ok")
    return 0


if __name__ == "__main__":
    if "--selftest" not in sys.argv:
        print("usage: manifest.py --selftest", file=sys.stderr)
        raise SystemExit(2)
    sys.exit(selftest())
