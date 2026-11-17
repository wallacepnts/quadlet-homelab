# The app manifest: `apps/<app>/app.json`

Everything an app says about itself lives in one file, next to its units. It is the model of
[CasaOS's app store](https://github.com/IceWhaleTech/CasaOS-AppStore) — there an app is a compose file
with an `x-casaos` block holding its metadata — in JSON of our own, beside the Quadlet units instead of
inside them.

A folder is therefore the units, the `.env.example` if there is one, this file, and the logo. There is no README
per app, no `install.ini`, no `notes.md`: the services table in the root READMEs is generated from the manifests,
and the panel shows the notes. Everything is written in English, once: there is no per-language copy to keep.

```json
{
  "title": "Memos",
  "tagline": "Quick notes, self-hosted and markdown-native",
  "category": "Productivity",
  "links": { "docs": "https://www.usememos.com/docs" },
  "notes": "The first user to sign up becomes admin…",
  "units": { "memos": { "upstream": "usememos/memos" } }
}
```

and, beside it, the logo and the screenshots as plain files:

```
apps/memos/
├── memos.container
├── app.json
├── icon.svg                 # the logo: icon.svg, .png, .webp or .jpg, up to 512 KB
└── screenshots/             # optional: 1.png, 2.png ... up to six, up to 1 MB each
```

## The fields

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | yes | The name shown in the store and in the services table. |
| `tagline` | yes | One short, plain sentence, up to 70 characters, with no dash or parenthesis: what the app is, as you would tell a friend (*A media server for your home collection.*). It is the description in the table and on the card. Caveats go in `notes`. |
| `category` | no | One of the groups in `qhui.GRUPOS` (the store's categories). Infrastructure with no place among them (homepage, postfix, toolbx) has none. |
| `links` | no | `docs` (the project's documentation, https), `repo` (`owner/repo` or a URL, only where the image's own path points at the wrong place). |
| `min_podman` | no | `"5.4"`: a floor above the 5.0 that `Notify=healthy` already needs. |
| `deprecated` | no | Text: why it is discontinued. The store offers no install. |
| `notes` | no | Markdown: what to do at the first run and what is odd about the app. The panel shows it. |
| `secrets` | per `Secret=` | `{"<secret>": "rand-hex 32"}`: how each secret is made (`rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`, `shell <cmd>`, `manual <text>`). |
| `validate` | no | `{"<secret>": "shell <cmd>"}`: a check of a `manual` secret that only the far end can judge. The value arrives on stdin. |
| `config` | no | `{"<file in the folder>": "<where it lands on the host>"}`: auxiliary files `qh` copies once and never overwrites. |
| `vars` | per `${VAR}` in a `Volume=` | `{"MEDIA_DATA_DIR": "~/data"}`: the systemd variables a unit uses, and the default the install offers. |
| `login` | no | `{"user": "admin", "password": "<secret>"}`, or `{"credentials": "<secret>"}` when one secret holds `user:password`: what the install prints. |
| `choices` | no | `{"VERSION": {"question": "…", "options": [{"value": "11", "label": "Windows 11"}, "10"]}}`: a pick from a fixed list that only matters on the first install. An option is `{value, label}` or just the value. The first is the default. |
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
`services:end` markers, comes from `title`, the logo file and `tagline`. `python3 check.py --readme` rewrites it, and
`check.py` fails when it is out of date.

## What the CasaOS format has that this does not

CasaOS carries `developer`, `author`, `architectures`, `tips.before_install`, `port_map`, `index`, `scheme`,
`thumbnail`, `release_notes`, a `description` apart from the `tagline`, translations, and a description for every
port, volume and environment variable. Here the architectures come from the registry, the port and the address from
the units, the release notes from GitHub, and the notes cover `tips`. Translations and the licence were left out on
purpose, and so were comments: why a recipe is shaped the way it is belongs in `docs/`, not in the manifest.

## Checking

`python3 check.py` validates every manifest: the required fields, the logo file, the category, the
shape of each object, an unknown top-level key (a typo), and the rules of each part (a recipe for every `Secret=`, a
`login` that names a real secret, a `vars` default for every `${VAR}` in a `Volume=`, the shape for every unit
without a tag). `python3 manifest.py --selftest` tests the reader.
