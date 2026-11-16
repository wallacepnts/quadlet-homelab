#!/usr/bin/env python3
"""`apps/<app>/app.json`: everything one app says about itself, in one file (spec 2).

The model is CasaOS's app store, where an app is a compose file with an `x-casaos` block that
carries its metadata, but in JSON of our own, beside the unit files instead of inside them:

    {
      "spec": 2,
      "id": "memos",                                  # the folder name
      "title": "Memos",
      "icon": "https://cdn.jsdelivr.net/.../memos.svg",
      "tagline": {"en": "Self-hosted quick notes", "pt": "Notas rápidas self-hosted"},
      "category": "Productivity",                     # one of qhui.GRUPOS
      "license": "MIT",
      "links": {"docs": "https://www.usememos.com/docs", "repo": "usememos/memos"},
      "screenshots": ["https://..."],                 # at most 6, https
      "works_with": ["ntfy"],                         # suggestions, never requirements
      "min_podman": "5.4",
      "deprecated": {"en": "why", "pt": "porquê"},    # no install is offered
      "notes": {"en": "markdown", "pt": "markdown"},  # first run, what is odd about it
      "secrets": {"memos-token": "rand-hex 32"},      # how each Secret= is made
      "validate": {"authkey": "shell ..."},           # a value only the far end can judge
      "config": {"nginx.conf": "%h/.config/.../nginx.conf"},
      "vars": {"MEDIA_DATA_DIR": "~/data"},           # systemd variables a Volume= uses, with a default
      "login": {"user": "admin", "password": "memos-token"},
      "choices": {"VERSION": {"question": "...", "options": [{"value": "11", "label": "..."}]}},
      "backup": {"mode": "stop", "exclude": ["upload/thumbs"]},
      "units": {
        "memos": {"upstream": "usememos/memos", "image": "{version}"}
      }
    }

Every entry that explains itself may be written `{"value": X, "note": "why"}` instead of `X`: JSON has
no comments, and the reason a recipe is shaped the way it is matters as much as the recipe.
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

SPEC = 2
FILE = "app.json"
LANGS = ("en", "pt")


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


def dump(data):
    """The canonical text of a manifest: two-space indent, keys in the order the spec lists them."""
    return json.dumps(ordered(data), ensure_ascii=False, indent=2) + "\n"


KEY_ORDER = ["spec", "id", "title", "icon", "tagline", "category", "license", "links", "screenshots",
             "works_with", "min_podman", "deprecated", "notes", "secrets", "validate", "config", "vars",
             "login", "choices", "backup", "units"]


def ordered(data):
    saida = {k: data[k] for k in KEY_ORDER if k in data}
    saida.update({k: v for k, v in data.items() if k not in saida})
    return saida


def unwrap(v):
    """`X` or `{"value": X, "note": ...}` -> X."""
    return v["value"] if isinstance(v, dict) and "value" in v else v


def note_of(v):
    return v.get("note") if isinstance(v, dict) else None


def wrap(value, note=None):
    return {"value": value, "note": note} if note else value


# -- the ConfigParser-shaped view -----------------------------------------------------------

class View:
    """What `configparser.ConfigParser` answered, from a manifest: sections, options, items, get.

    The names of the sections are the ones install.ini used (`secrets`, `upstream`, `image`, `store`,
    `backup`, `config`, `vars`, `validate`, `login`, `login.<unit>`, `choices`, `choices.<unit>`), so the
    code that asked those questions did not have to change when the file did."""

    def __init__(self, data):
        self.data = data or {}
        self._s = self._build(self.data)

    @staticmethod
    def _lines(valor):
        return "\n".join(valor) if isinstance(valor, list) else valor

    def _build(self, d):
        s = {}

        def pairs(secao, mapa):
            if mapa:
                s.setdefault(secao, {}).update({k: unwrap(v) for k, v in mapa.items()})

        pairs("secrets", d.get("secrets"))
        pairs("validate", d.get("validate"))
        pairs("config", d.get("config"))
        pairs("vars", d.get("vars"))
        login = d.get("login")
        if login:
            s["login"] = {k: unwrap(v) for k, v in login.items()}
        upstream, image = {}, {}
        for unit, u in (d.get("units") or {}).items():
            if "upstream" in u:
                upstream[unit] = unwrap(u["upstream"])
            if "image" in u:
                image[unit] = unwrap(u["image"])
            if u.get("login"):
                s[f"login.{unit}"] = {k: unwrap(v) for k, v in u["login"].items()}
            if u.get("choices"):
                s[f"choices.{unit}"] = {k: self._choice(v) for k, v in u["choices"].items()}
        if upstream:
            s["upstream"] = upstream
        if image:
            s["image"] = image
        if d.get("choices"):
            s["choices"] = {k: self._choice(v) for k, v in d["choices"].items()}
        loja = {}
        for chave in ("category", "license"):
            if d.get(chave):
                loja["group" if chave == "category" else chave] = d[chave]
        links = d.get("links") or {}
        for chave in ("docs", "repo"):
            if links.get(chave):
                loja[chave] = links[chave]
        if d.get("screenshots"):
            loja["screenshots"] = "\n".join(d["screenshots"])
        if d.get("works_with"):
            loja["works_with"] = ", ".join(d["works_with"])
        if d.get("min_podman"):
            loja["min_podman"] = d["min_podman"]
        dep = d.get("deprecated")
        if dep:
            loja["deprecated"] = dep.get("en", "")
            if dep.get("pt"):
                loja["deprecated_pt"] = dep["pt"]
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
        c = unwrap(c)
        return "\n".join([c["question"]] + [f"{o['value']}: {o['label']}" if o.get("label") else o["value"]
                                            for o in c["options"]])

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
    return View(load(folder))


# -- validation -------------------------------------------------------------------------------

def problems(data, folder_name, grupos, existing=None):
    """What is wrong with a manifest, as a list of messages; empty when it holds."""
    erros = []
    if data.get("spec") != SPEC:
        erros.append(f'"spec" must be {SPEC}')
    if data.get("id") != folder_name:
        erros.append(f'"id" is {data.get("id")!r}, the folder is {folder_name!r}')
    for k in ("title", "icon"):          # `category` is optional: infrastructure (homepage, postfix) has none
        if not data.get(k):
            erros.append(f'"{k}" is required')
    if data.get("category") and data["category"] not in grupos:
        erros.append(f'"category" {data["category"]!r} is not one of: {", ".join(grupos)}')
    tag = data.get("tagline")
    if not isinstance(tag, dict) or not all(isinstance(tag.get(l), str) and tag.get(l).strip() for l in LANGS):
        erros.append('"tagline" needs a non-empty "en" and "pt"')
    icon = data.get("icon", "")
    if icon and not re.fullmatch(r"https://\S+", icon):
        erros.append('"icon" is not an https:// URL')
    for k in ("secrets", "validate", "config", "vars"):
        if k in data and not isinstance(data[k], dict):
            erros.append(f'"{k}" must be an object')
    if "units" in data and not isinstance(data["units"], dict):
        erros.append('"units" must be an object')
    desconhecidas = set(data) - set(KEY_ORDER)
    if desconhecidas:
        erros.append(f"unknown key(s): {', '.join(sorted(desconhecidas))}")
    return erros


# -- the services table in the READMEs ---------------------------------------------------------

TABLE_BEGIN = "<!-- services:begin (generated from apps/*/app.json: python3 check.py --readme) -->"
TABLE_END = "<!-- services:end -->"
HEAD = {"en": ("Logo", "Application", "Description"), "pt": ("Logo", "Aplicativo", "Descrição")}


def services_table(apps, lang):
    """The markdown table of every app: logo, name linked to its folder, one-line description."""
    prefixo = "./apps/" if lang == "en" else "../../apps/"
    cab = HEAD[lang]
    linhas = [f"| {cab[0]} | {cab[1]} | {cab[2]} |", "| --- | --- | --- |"]
    for d in sorted(apps, key=lambda x: x["title"].casefold()):
        linhas.append(f'| <img src="{d["icon"]}" width="48" height="48" alt=""> | '
                      f'[{d["title"]}]({prefixo}{d["id"]}) | {d["tagline"][lang]} |')
    return "\n".join(linhas)


def splice(readme_text, tabela):
    """The README with the table between its markers replaced (the markers are added on first use)."""
    if TABLE_BEGIN in readme_text and TABLE_END in readme_text:
        a = readme_text.index(TABLE_BEGIN) + len(TABLE_BEGIN)
        b = readme_text.index(TABLE_END)
        return readme_text[:a] + "\n\n" + tabela + "\n\n" + readme_text[b:]
    return None


def selftest():
    d = {"spec": 2, "id": "x", "title": "X", "icon": "https://i/x.svg", "category": "Tools",
         "tagline": {"en": "a", "pt": "b"}, "license": "MIT", "links": {"docs": "https://d", "repo": "o/r"},
         "screenshots": ["https://a", "https://b"], "works_with": ["p", "q"], "min_podman": "5.4",
         "deprecated": {"en": "gone", "pt": "foi"},
         "secrets": {"s1": "rand-hex 8", "s2": {"value": "shell x", "note": "because"}},
         "config": {"c.conf": "%h/c"}, "vars": {"V": "~/v"}, "validate": {"s1": "shell y"},
         "login": {"user": "u", "password": "s1"},
         "choices": {"VERSION": {"question": "Which?", "options": [{"value": "1", "label": "One"}, {"value": "2"}]}},
         "backup": {"mode": "stop", "exclude": ["a/b", "c"]},
         "units": {"x": {"upstream": "o/r", "image": "v{version}"},
                   "y": {"upstream": {"value": "-", "note": "infra"}, "login": {"user": "z", "password": "s2"},
                         "choices": {"K": {"question": "Q", "options": [{"value": "a", "label": "A"}]}}}}}
    v = View(d)
    assert v.get("secrets", "s2") == "shell x" and v.get("secrets", "s1") == "rand-hex 8", "a note is not part of the value"
    assert note_of(d["secrets"]["s2"]) == "because" and note_of("plain") is None
    assert v.items("upstream") == [("x", "o/r"), ("y", "-")] and v.items("image") == [("x", "v{version}")]
    assert v.get("store", "group") == "Tools" and v.get("store", "screenshots") == "https://a\nhttps://b"
    assert v.get("store", "works_with") == "p, q" and v.get("store", "deprecated_pt") == "foi"
    assert v.get("backup", "exclude") == "\na/b\nc" and v.get("backup", "mode") == "stop"
    assert v.get("choices", "VERSION") == "Which?\n1: One\n2" and v.get("choices.y", "K") == "Q\na: A"
    assert v.get("login.y", "user") == "z" and v.get("login", "password") == "s1"
    assert v.has_section("vars") and not v.has_section("nope") and v.get("nope", "k", fallback="f") == "f"
    assert set(v.sections()) >= {"secrets", "upstream", "image", "store", "backup", "config", "vars", "validate",
                                 "login", "login.y", "choices", "choices.y"}
    assert dump(d).startswith('{\n  "spec": 2,\n  "id": "x"')
    assert problems(d, "x", ("Tools",)) == [] and problems({**d, "id": "z"}, "x", ("Tools",))
    assert problems({**d, "tagline": {"en": "a"}}, "x", ("Tools",)) and problems({**d, "category": "Nope"}, "x", ("Tools",))
    assert problems({**d, "wat": 1}, "x", ("Tools",)), "an unknown key is a typo"
    tab = services_table([d, {**d, "id": "a", "title": "a-first", "tagline": {"en": "e", "pt": "p"}}], "pt")
    assert tab.splitlines()[0] == "| Logo | Aplicativo | Descrição |" and "[a-first](../../apps/a) | p |" in tab.splitlines()[2], tab
    assert splice("a\n" + TABLE_BEGIN + "\nold\n" + TABLE_END + "\nz", "T").count("T") == 1
    assert splice("no markers", "T") is None
    print("manifest selftest: ok")
    return 0


if __name__ == "__main__":
    if "--selftest" not in sys.argv:
        print("usage: manifest.py --selftest", file=sys.stderr)
        raise SystemExit(2)
    sys.exit(selftest())
