# The app manifest: `apps/<app>/app.json`

Everything an app says about itself lives in one file, next to its units. It is the model of
[CasaOS's app store](https://github.com/IceWhaleTech/CasaOS-AppStore) — there an app is a compose file
with an `x-casaos` block holding its metadata — in JSON of our own, beside the Quadlet units instead of
inside them.

A folder is therefore the units, the `.env.example` if there is one, this file, and the logo. There is no README
per app and no `install.ini`: the services table in the root READMEs is generated from the manifests, and the panel shows
the notes. The descriptions and the notes are written in English and Portuguese.

```json
{
  "title": "Memos",
  "short_desc": { "en": "Quick notes.", "pt": "Notas rápidas." },
  "description": { "en": "…", "pt": "…" },
  "author": "usememos",
  "source": "https://github.com/usememos/memos",
  "docs": "https://www.usememos.com/docs",
  "category": "Productivity",
  "units": { "memos": { "upstream": "usememos/memos" } }
}
```

Each file starts with `"$schema": "../app-schema.json"`, which makes the editor (Zed, VS Code) complete the keys
and underline a wrong one while you type. `apps/app-schema.json` is built from `manifest.py`
(`python3 check.py --schema` rewrites it, and `check.py` fails when it is stale).

The text is canonical, the way Runtipi writes its `config.json`: one key per line, keys in the order of the table
below, a short object or list kept on its line (`"units": { "memos": { "upstream": "usememos/memos" } }`) and one
that would pass 110 columns (an `{en, pt}` pair with a long text, say) broken into one entry per line. Do not format it by hand: write it any way and run `python3 check.py --format`, which
`check.py` also demands.

and, beside it, the logo and the screenshots as plain files:

```
apps/memos/
├── memos.container
├── app.json
├── notes.en.md              # only for an app that needs one: what to do first, and notes.pt.md beside it
├── icon.svg                 # the logo: icon.svg, .png, .webp or .jpg, up to 512 KB
└── screenshots/             # optional: 1.png, 2.png ... up to six, up to 1 MB each
```

## The notes

`notes.en.md` and `notes.pt.md` hold what the person has to do at the first run, or what could hurt them: turn signup
off, change a default password, a library that has to be put in place. **Only an app that needs one has them**, always
both languages, up to 2,500 characters each (`check.py` enforces both). Anything longer, or about how the unit is built,
belongs in `docs/` (the measured hardening is in `docs/hardening.md`). The panel shows them in the app's screen.

## The fields

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | yes | The name shown in the store and in the services table. |
| `short_desc` | yes | `{en, pt}`: one short, plain sentence each, up to 70 characters, no dash or parenthesis (*A media server for your home collection.*). It is the description in the table and on the card. Caveats go in `notes`. |
| `description` | yes | `{en, pt}`: what the app is, in a few lines. The panel shows it when the app is opened. |
| `author` | no | Who makes the project (the owner of `source`). |
| `source` | no | The project's repository, an https URL. The panel links it, and the issues and releases come from it. |
| `website` | no | The project's home page, an https URL. |
| `docs` | no | The project's documentation, an https URL. |
| `architectures` | no | `["amd64", "arm64"]`: what the image runs on, when known (the panel asks the registry too). |
| `category` | no | One of the groups in `qhui.GRUPOS` (the store's categories). Infrastructure with no place among them (homepage, postfix, toolbx) has none. |
| `min_podman` | no | `"6.1"`: a floor above the 6.0 every app already needs, for a unit that uses a Quadlet key newer than that. Never below 6.0 (`check.py` refuses it). |
| `requires_https` | no | `true`: the app breaks over plain HTTP (a vault, a service worker). The panel warns when it is reached by the local network only. |
| `no_gui` | no | `true`: the app has no web interface (a runner, a mail relay, a toolbox); the store shows no address and no Open button, whatever port it publishes. |
| `deprecated` | no | Text: why it is discontinued. The store offers no install. |
| `secrets` | per `Secret=` | `{"<secret>": "rand-hex 32"}`: how each secret is made (`rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`, `shell <cmd>`, `manual <text>`). |
| `validate` | no | `{"<secret>": "shell <cmd>"}`: a check of a `manual` secret that only the far end can judge. The value arrives on stdin. |
| `config` | no | `{"<file in the folder>": "<where it lands on the host>"}`: auxiliary files `qh` copies once and never overwrites. |
| `vars` | per `${VAR}` in a `Volume=` | `{"MEDIA_DATA_DIR": "~/data"}`: the systemd variables a unit uses, and the default the install offers. |
| `ask` | no | `{"<manual secret or vars name>": {"type": "password", "label": {"en": "…", "pt": "…"}, "hint": "…", "min": 12, "max": 64, "regex": "…", "pattern_error": "…", "required": true}}`: how the install form asks it, the way Runtipi's `form_fields` does. `type` is `text` (default), `password`, `email`, `number`, `url` or `path`; `label`, `hint`, `placeholder` and `pattern_error` are a text or an `{en, pt}` pair; `min`/`max` are a length (a range for `number`); `regex` must match the whole value. The browser checks it as you type and the server checks again before anything is installed. |
| `login` | no | `{"user": "admin", "password": "<secret>"}`, or `{"credentials": "<secret>"}` when one secret holds `user:password`: what the install prints. |
| `choices` | no | `{"VERSION": {"question": "…", "options": [{"value": "11", "label": "Windows 11"}, "10"]}}`: a pick from a fixed list that only matters on the first install. An option is `{value, label}` or just the value. The first is the default. |
| `options` | no | `{"database": {"question": "…", "default": "sqlite", "values": {"sqlite": {"label": "SQLite"}, "postgres": {"label": "PostgreSQL", "units": ["app-postgres"], "env": {"DB_HOST": "…"}, "secrets": ["app-db-password"]}}}}`: a choice the developer offers at the first install. A value names the optional `units` it switches on, the `env` variables it adds to the `.env` and the `secrets` it needs (each with a recipe in `secrets`). A unit no value names is always on. At least two values; `default` is one of them. |
| `widgets` | no | `[{"type": "immich"}, {"type": "sonarr", "unit": "media-stack-sonarr"}]`: a few numbers from inside the app, shown on its tile and in its panel (photos in Immich, blocked queries in AdGuard…). `type` is one the store can read (`svcwidgets.TYPES`: immich, adguard, paperless, uptime-kuma, sonarr, radarr, jellyfin); `unit` only in a folder of several. The key each one needs is typed in the panel and kept on the server, never in the manifest. |
| `icon` | no | `{"bg": "#12352a", "fit": 1.2, "tone": "dark"}`: how the logo sits on its plate in the panel, each key optional. `bg` is the plate's colour (for a logo that does not show on the automatic one); `fit` (0.8 to 1.4) scales the logo, which the panel measures itself otherwise; `tone` is `light`, `color`, `dark` or `full` (the logo fills the plate). |
| `backup` | no | `{"mode": "stop", "exclude": ["upload/thumbs"]}`: stop the service for the copy, and the folders that rebuild themselves. |
| `units` | no | Per unit, below. |

## `units`

One entry per `.container` that needs one, keyed by the unit's basename:

| Field | Meaning |
| --- | --- |
| `upstream` | Where its version comes from: `owner/repo` (a GitHub release), `registry:<regex>`, `compose:<owner>/<repo>:<file>` (a sidecar pinned to what the app's compose validates), or `-` (nothing comparable). Left out, it is derived from the image name where the convention holds (`ghcr.io/<org>/<repo>`, `docker.io/<org>/<repo>`). |
| `image` | The shape of its tag when it is not just the version: `v{version}`, `{version}-alpine`, `{version:2}`. A unit whose `Image=` has **no tag** is a release-following image, `qh` pins the latest release on the host (see [auto-update](./auto-update.md)), and the shape is `{version}` unless this says otherwise. |
| `login`, `choices` | As above, for a folder of independent services that do not share one. |

## Generated, not written

The services table in `README.md` and `docs/pt-BR/README.md`, between the `services:begin` and
`services:end` markers, comes from `title`, the logo file and `short_desc`. `python3 check.py --readme` rewrites it, and
`check.py` fails when it is out of date.

## What the CasaOS format has that this does not

CasaOS carries `developer`, `tips.before_install`, `port_map`, `index`, `scheme`,
`thumbnail`, `release_notes`, and a description for every
port, volume and environment variable. Here the architectures come from the registry, the port and the address from
the units, the release notes from GitHub, and the notes cover `tips`. The licence was left out on
purpose, and so were comments: why a recipe is shaped the way it is belongs in `docs/`, not in the manifest.

## Checking

`python3 check.py` validates every manifest: the required fields, the logo file, the category, the
shape of each object, an unknown top-level key (a typo), and the rules of each part (a recipe for every `Secret=`, a
`login` that names a real secret, a `vars` default for every `${VAR}` in a `Volume=`, the shape for every unit
without a tag). `python3 manifest.py --selftest` tests the reader.
