# CookCLI — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [CookCLI](https://github.com/cooklang/cookcli) ([CookLang](https://cooklang.org)
recipe server) deploy via Podman Quadlet, using the official
`ghcr.io/cooklang/cookcli` image.

## Architecture

A single container, Rust. **No database, and that is the point**: the
recipes *are* `.cook` files in a folder. You write them in a text editor,
version them in git, and the server just reads and renders them — with the
shopping list and portion scaling computed on the fly.

```cook
---
title: Café com leite
servings: 1
---

Esquente o @leite{200%ml} e misture com o @café{50%ml}.
```

It is the opposite of a manager with a database and forms: here the recipe
is version-controlled text, editable in any editor.

(The example recipes shipped here are in Portuguese — they are the user's own
content, and `aisle.conf` matches their ingredient names.)

### `UserNS=keep-id`, not `User=`

The image **refuses to start** when the process's uid does not match the
recipes folder's owner — it stops and literally prints:

```
cookcli:
  user: "1000:1000"  # <-- change to match your host user
```

The `User=1000` rung passes the hardening test, but it is beside the point
here: the recipes folder is **your editing area**, and with `User=` it would
come to belong to a subuid you cannot write to. It is the same trade-off as
[vaultzap](../vaultzap/)'s `inbox`.

`UserNS=keep-id` solves both sides: the process runs as your uid, the folder
stays yours, and cookcli is happy. This is not hardening
([rule 20](../../docs/conventions.md)), it is a choice of owner.

### No healthcheck, and why

The image carries only the `cook` binary and `dash` — no `wget`, `curl`, `nc`
or `python3` to make a request from inside. With no HTTP client there is no
honest healthcheck, so the unit has neither `HealthCmd` nor `Notify=healthy`
(which would require one, by rule 14). What is left is the container's
lifecycle: `cook server` is PID 1, and if it dies `Restart=always` brings it
back.

## Files

```
cookcli.container      # main unit
aisle.conf.example     # the shop's aisles, for the shopping list
pantry.conf.example    # what you already have at home, subtracted from the list
```

## Installation

```bash
python3 install.py cookcli            # dry-run: shows what it will do
python3 install.py cookcli --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:9080` (or through [tsdproxy](../tsdproxy/) at
`https://cookcli.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/cookcli.container

# 2. The recipes folder. Do NOT chown it here: it is yours, and the unit's
#    keep-id is precisely what makes the container accept that.
mkdir -p ~/.config/containers/volumes/cookcli/recipes

# 3. Start it
systemctl --user daemon-reload
systemctl --user start cookcli
```

Open `http://<host-ip>:9080` (or through [tsdproxy](../tsdproxy/) at
`https://cookcli.<your-tailnet>.ts.net`).

</details>

## Writing recipes

One `.cook` file per recipe, inside `recipes/`. A subfolder becomes a
category. The server reloads by itself — no restart needed.

```bash
cat > ~/.config/containers/volumes/cookcli/recipes/pao-de-queijo.cook <<'EOF'
---
title: Pão de queijo
servings: 12
---

Misture @polvilho azedo{500%g} com @queijo meia-cura ralado{300%g}.
Asse por ~{25%minutos} no #forno{} a 200°C.
EOF
```

`@ingredient{quantity%unit}`, `#equipment{}`, `~{time}`. The whole syntax is
in the [specification](https://cooklang.org/docs/spec/).

**Versioning it in git is the natural use**: the folder is just text.

## Photos in recipes

By **naming convention**, with nothing to configure: the image has the same
name as the `.cook` file, in the same folder.

```
recipes/
├── bolo.cook
├── bolo.jpg        ← becomes bolo's photo
├── pao-de-queijo.cook
└── pao-de-queijo.png
```

The extensions that work, tested on this version: **`.jpg`, `.jpeg`, `.png`,
`.webp`**. `.gif` is silently ignored — the recipe appears without a photo and
nothing reports it.

No restart needed: drop the file into the folder and reload the page. The
image is then served at `/api/static/<name>.<ext>`.

**One photo per recipe.** I tested the per-step image convention
(`bolo.0.jpg`, `bolo.1.jpg`) and this version of the server **does not expose
it** — the files sit in the folder without appearing, and the recipe's image
field comes back empty. To illustrate steps, the route would be embedding the
image in the recipe's text as Markdown.

## What else fits in a recipe

Tested on this version against the running instance — the
[spec's canonical list](https://github.com/cooklang/spec/blob/main/proposals/0007-canonical-metadata.md)
has 16 fields, and **the interface shows 12**:

| Shown on the page | Accepted but **not** displayed |
| --- | --- |
| `description`, `author`, `source`, `course`, `cuisine`, `difficulty`, `tags`, `servings`, `prep time`, `cook time` | `introduction`, `diet`, `time required`, `locale` |

The four on the right do not disappear — they come back in the API, so they
serve for organisation and for external tooling. They simply have no place on
screen. Note that `time required` is ignored when `prep time` and `cook time`
both exist.

Beyond the metadata, two constructs of the syntax itself go a long way:

- **Sections**: `== Preparo ==` breaks the recipe into titled blocks.
- **Notes**: a line beginning with `>` becomes a highlighted block, outside
  the list of steps — good for a tip, an ingredient substitution, a warning.

This directory's
[`bolo-de-cenoura.cook.example`](./bolo-de-cenoura.cook.example) uses **every**
feature of the syntax at once, and
[`calda-de-chocolate.cook.example`](./calda-de-chocolate.cook.example) exists
to demonstrate references between recipes. See "The reference recipe" below.

### The reference recipe

`bolo-de-cenoura.cook.example` exercises the whole spec. Every one of its
lines was verified against this version's API:

| Feature | Syntax |
| --- | --- |
| an ingredient with a compound name | `@farinha de trigo{}` |
| quantity and unit | `@óleo{200%ml}` |
| **a short preparation note** | `@cenoura{3}(média, em rodelas)` |
| equipment | `#liquidificador{}` |
| **a named timer** | `~forno{40%minutos}` |
| a section | `= Massa`, `== Forno ==` |
| a note | a line beginning with `>` |
| a line comment | `-- disappears from the page` |
| a block comment | `[- also disappears -]` |
| a line break inside a step | a backslash at the end of the line |
| **a reference to another recipe** | `@./molhos/calda-de-chocolate{200%ml}` |

Two worth highlighting because they are not obvious:

**The short preparation note goes into the ingredient list, not the text.**
Writing `@cenoura{3}(média, em rodelas)` makes "(média, em rodelas)" appear
next to the carrot in the list — which is what lets you get everything chopped
before you start.

**A reference between recipes adds to the shopping list.** The cake references
the sauce, and its shopping list carries chocolate and cream, which only exist
in the sauce:

```
[hortifruti]   cenoura        3
[laticínios]   creme de leite 50 ml
               ovo            3
[mercearia]    chocolate      150 g
               fermento em pó 1 colher de sopa
               óleo           200 ml
```

Flour, sugar and butter do not appear because they are in `pantry.conf`. The
reference accepts `{2}` (doubling the whole recipe), `{4%servings}` (reading
the target's `servings`) and `{200%ml}` (reading its `yield`) — the sauce
declares `yield: 200%ml` for exactly that.

**Scaling works on the whole file**: `cook recipe read bolo-de-cenoura.cook:2`
doubles everything, including what comes from the referenced recipe.

### Meal plans: `.menu` files

A `.menu` is a Cooklang file that uses **sections as days** and references to
pull in the recipes. This directory's
[`semana.menu.example`](./semana.menu.example) is one.

```cooklang
---
title: Cardápio da semana
servings: 4
---

== Segunda (2026-08-10) ==

@./cafe-com-leite{2}
@./bolo-de-cenoura{4%servings}

== Terça (2026-08-11) ==

@./bolo{1}
```

The parenthesised date in `YYYY-MM-DD` is recognised — the API returns a
separate `date` field, and applications use it to highlight today.

The real gain is the whole week's shopping list, adding everything up and
already subtracting the pantry:

```bash
podman exec cookcli sh -c 'cd /recipes && cook shopping-list semana.menu'
```

**Where it shows up**: there is no `/menus` route in the interface — the
`.menu` appears in the list alongside the recipes and opens at
`/recipe/<name>`, rendering the days, the dates and the scaled references. The
API has a route of its own (`/api/menus`), but the UI does not.

### Two traps with references between recipes

**1. The reference uses the FILE NAME, not the title.** Writing
`@./bolo simples{1}` for a recipe whose file is `bolo.cook` fails with
`Invalid recipe path: bolo simples`. Worse: **the interface renders the meal
plan normally**, showing "bolo simples (×1)" — only the shopping list reports
it.

**2. Do not use a unit in the reference: use `{N}` or `{N%servings}`.**
`yield` is not supported in this version — the sauce itself produces
`Unsupported value for key: 'yield'`. And the worst part is the
inconsistency: the same reference `@./molhos/calda-de-chocolate{200%ml}`
resolves as **×1** when the list comes from the recipe, and as **×200** when
it comes from a meal plan that references that recipe. I found this out
because the week's list asked for **15 kg of chocolate**.

With `{1}`, the numbers add up: the week's list asks for 225 g of chocolate —
150 g from the sauce referenced directly in the meal plan, plus 75 g from the
cake, which enters at half a recipe because of the `{4%servings}` against its
`servings: 8`.

### Video and per-ingredient photos: not possible

Three things that do **not** exist, all verified:

- **Video has neither a field nor a convention.** A `recipe.mp4` next to the
  `.cook` sits in the folder unreferenced — even though it is *served* at
  `/api/static/recipe.mp4`, because the whole folder is static. That is: the
  file is reachable by URL, but nothing in the interface points at it.
- **A per-ingredient photo does not exist** in the spec or in the server.
- **Markdown and HTML in a step's text are not rendered.** I tested
  `![photo](...)`, `[link](...)` and `<img src=...>`: all three appear as
  plain text on the page. So there is no working around it by embedding media
  in a step.

Add to that what was already documented: **a per-step image** (`bolo.0.jpg`)
is not exposed either. In practice, CookCLI accepts **one photo per recipe**
and no other media.

### `image:` in the metadata beats the file

If the recipe has `image: https://...` in its frontmatter, that value
**replaces** the file convention — even with a `recipe.jpg` in the folder, the
URL is what counts. Useful for pointing at a photo hosted elsewhere;
treacherous if you leave the URL there and later cannot work out why the local
file is being ignored.

## The shopping list: `aisle.conf` and `pantry.conf`

Two optional files in `recipes/config/` that turn the shopping list from an
"ingredient dump" into something usable:

| File | What it does |
| --- | --- |
| `aisle.conf` | groups by shop aisle, in the order you walk down them |
| `pantry.conf` | what you already have at home — CookCLI **subtracts** it from the list |

```bash
mkdir -p ~/.config/containers/volumes/cookcli/recipes/config
wget -O ~/.config/containers/volumes/cookcli/recipes/config/aisle.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/aisle.conf.example
wget -O ~/.config/containers/volumes/cookcli/recipes/config/pantry.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/pantry.conf.example
```

No restart needed — the server re-reads both. Check with:

```bash
podman exec cookcli sh -c 'cd /recipes && cook doctor'
```

### The fourth, and the most misleading: `WorkingDir`

If the **Preferences** page says

```
Aisle Configuration: Not configured
Pantry Configuration: Not configured
```

the files are there and the server is looking in the wrong place. cookcli
looks for `./config/` **relative to the process's working directory**, not to
the recipes folder — and the container's is `/`, so it looks in `/config`. The
unit fixes it with `WorkingDir=/recipes`.

What makes this treacherous is the silence: nothing fails, the server comes up
normally, and the shopping list simply comes out with no categories and
without subtracting the pantry. And `cook doctor` does **not** reproduce the
problem, because you run it with `cd /recipes` — which is exactly how I
validated the files and concluded everything was fine.

### Three traps, all found by testing

**1. `aisle.conf` does not accept comments.** It is neither TOML nor INI: it
is a format of its own, and every line outside a `[...]` section is read as an
ingredient. A header with `#` becomes `Ingredient found before any category`,
once per line. That is why the `aisle.conf.example` here starts straight at
`[hortifruti]`, with the explanation in this README.

**2. `pantry.conf` is TOML, and accents break it.** A section or item name
with an accent or a space **needs quotes** — `[armário]` takes the whole file
down with `Failed to parse pantry file`, and the list comes out as though you
had nothing at home. Use `[armario]` without the accent for the section, and
`"açúcar" = ...` with quotes for the item.

**3. The unit has to match for the subtraction to happen.** A recipe asking
for `300%g` of flour with the pantry saying `1%kg` produces
`Unit mismatch for 'farinha de trigo'` and the item **stays on the list**.
That is why the example stores flour and sugar in `g`, not in `kg`.

With both in place, a cake recipe calling for flour, sugar, eggs, butter and
baking powder produces only what is missing:

```
[laticínios]
ovo            3
[other]
fermento em pó 10 g
```

### Recipe syntax: use frontmatter

The `>>` form for metadata **is deprecated** — CookCLI warns
`The '>>' syntax for metadata is deprecated, use a YAML frontmatter`. Write it
like this:

```cook
---
title: Bolo simples
servings: 8
---

Misture @farinha de trigo{300%g} com @açúcar{200%g} e @ovos{3}.
```

## Security

**There is no authentication.** Whoever reaches the port reads and edits the
recipes through the UI. On the tailnet that is acceptable; to put a login in
front of it, the route is [Authentik](../authentik/).

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.32.1`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The official self-hosting post still cites `0.23.0`, well behind — always
check the releases page, not the tutorial.

## Backup & recovery

```bash
tar -czf cookcli-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes cookcli
```

There is no need to stop the service: they are text files the server only
reads. If the folder is in git, the backup is already the `push`.

## Useful commands

```bash
systemctl --user status cookcli
podman logs -f cookcli
podman exec cookcli cook recipe read /recipes/pao-de-queijo.cook
```

## Credits

Quadlet deploy based on [CookCLI](https://github.com/cooklang/cookcli)
do projeto [CookLang](https://cooklang.org) (MIT).
