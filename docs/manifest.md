# The app manifest: `apps/<app>/app.json`

Everything an app says about itself lives in one file, next to its units. It is the model of
[CasaOS's app store](https://github.com/IceWhaleTech/CasaOS-AppStore) — there an app is a compose file
with an `x-casaos` block holding its metadata — in JSON of our own, beside the Quadlet units instead of
inside them. `"spec": 2` is the version of this format.

A folder is therefore the units, the `.env.example` if there is one, and this file. There is no README per
app, no `install.ini`, no `notes.md`: the services table in the root READMEs is generated from the
manifests, and the panel shows the notes.

```json
{
  "spec": 2,
  "id": "memos",
  "title": "Memos",
  "icon": "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg",
  "tagline": { "en": "Quick notes, self-hosted and markdown-native", "pt": "Notas rápidas, self-hosted e markdown-nativo" },
  "category": "Productivity",
  "license": "MIT",
  "links": { "docs": "https://www.usememos.com/docs" },
  "screenshots": ["https://..."],
  "notes": { "en": "Open the page and create the account…", "pt": "Abra a página e crie a conta…" },
  "units": { "memos": { "upstream": "usememos/memos", "image": "{version}" } }
}
```

## The fields

| Field | Required | Meaning |
| --- | --- | --- |
| `spec` | yes | `2`. |
| `id` | yes | The folder name. `check.py` fails a mismatch. |
| `title` | yes | The name shown in the store and in the services table. |
| `icon` | yes | An `https://` image. |
| `tagline` | yes | One line, `{"en": …, "pt": …}`: the description in the table and on the card. |
| `category` | no | One of the groups in `qhui.GRUPOS` (the store's categories). Infrastructure with no place among them (homepage, postfix, toolbx) has none. |
| `license` | no | The project's licence, one short line. Shown beside the notes. |
| `links` | no | `docs` (the project's documentation, https), `repo` (`owner/repo` or a URL, only where the image's own path points at the wrong place). |
| `screenshots` | no | Up to six `https://` images the project itself hosts, no repeats. |
| `works_with` | no | Other app folders worth running beside this one. A suggestion, never a requirement. |
| `min_podman` | no | `"5.4"`: a floor above the 5.0 that `Notify=healthy` already needs. |
| `deprecated` | no | `{"en": …, "pt": …}`: why it is discontinued. The store offers no install. |
| `notes` | no | Markdown, per language: what to do at the first run and what is odd about the app. The panel shows it. |
| `secrets` | per `Secret=` | `{"<secret>": "rand-hex 32"}`: how each secret is made (`rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`, `shell <cmd>`, `manual <text>`). |
| `validate` | no | `{"<secret>": "shell <cmd>"}`: a check of a `manual` secret that only the far end can judge. The value arrives on stdin. |
| `config` | no | `{"<file in the folder>": "<where it lands on the host>"}`: auxiliary files `qh` copies once and never overwrites. |
| `vars` | per `${VAR}` in a `Volume=` | `{"MEDIA_DATA_DIR": "~/data"}`: the systemd variables a unit uses, and the default the install offers. |
| `login` | no | `{"user": "admin", "password": "<secret>"}`, or `{"credentials": "<secret>"}` when one secret holds `user:password`: what the install prints. |
| `choices` | no | `{"VERSION": {"question": "…", "options": [{"value": "11", "label": "Windows 11"}]}}`: a pick from a fixed list that only matters on the first install. The first option is the default. |
| `backup` | no | `{"mode": "stop", "exclude": ["upload/thumbs"], "note": "…"}`: stop the service for the copy, and the folders that rebuild themselves. |
| `units` | no | Per unit, below. |

## `units`

One entry per `.container` that needs one, keyed by the unit's basename:

| Field | Meaning |
| --- | --- |
| `upstream` | Where its version comes from: `owner/repo` (a GitHub release), `registry:<regex>`, `compose:<owner>/<repo>:<file>` (a sidecar pinned to what the app's compose validates), or `-` (nothing comparable). |
| `image` | The shape of its tag, `v{version}`, `{version}-alpine`, `{version:2}`. Present, the unit's `Image=` has **no tag**, and `qh` pins the latest release on the host (see [auto-update](./auto-update.md)). |
| `login`, `choices` | As above, for a folder of independent services that do not share one. |

## Explaining an entry

JSON has no comments, and why a recipe is shaped the way it is matters as much as the recipe. Any entry
of `secrets`, `config`, `vars`, `validate`, `login` or a unit's `upstream`/`image` can be written
`{"value": X, "note": "why"}` instead of `X`; the note is for people, and nothing reads it.

## Generated, not written

The services table in `README.md` and `docs/pt-BR/README.md`, between the `services:begin` and
`services:end` markers, comes from `title`, `icon` and `tagline`. `python3 check.py --readme` rewrites it, and
`check.py` fails when it is out of date.

## What the CasaOS format has that this does not (yet)

CasaOS carries `developer`, `author`, `architectures`, `tips.before_install`, `port_map`, `index`, `scheme`,
`thumbnail`, `release_notes` and a `description` apart from the `tagline`, plus a description for every port,
volume and environment variable. Here the architectures come from the registry, the port and the address
from the units, the release notes from GitHub, and the notes cover `tips`. None of these is read today; they
can be added to the manifest without changing its spec number, as new optional fields.

## Checking

`python3 check.py` validates every manifest: the spec number, `id`, the required fields, the category, the
shape of each object, an unknown top-level key (a typo), and the rules of each part (a recipe for every
`Secret=`, a `login` that names a real secret, a `vars` default for every `${VAR}` in a `Volume=`, the
`image` template for every unit without a tag). `python3 manifest.py --selftest` tests the reader.
