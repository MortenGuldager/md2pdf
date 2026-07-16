<!-- ═══════════════════════════════════════════════════════════════════════
     AGENT QUICKSTART  ·  read THIS, not the source
     ═══════════════════════════════════════════════════════════════════════
You are an AI agent asked to "make this .md a nice PDF" / "render with md2pdf".
Everything you need is in this block. Do NOT read src/ — the CLI is self-
describing (`md2pdf render --help`, `md2pdf templates`). Just serve the files
the way described below and run it.

1. Have the files on disk:  a `guide.md`, and any images it references with a
   RELATIVE path, e.g. `![caption](screenshots/01.png)`, sitting in that same
   folder. Caption text = the image's alt-text.

2. Run (no install; needs `uv` — `pip install uv` or https://astral.sh/uv):

     uvx --from git+https://github.com/MortenGuldager/md2pdf@main \
         md2pdf render guide.md -o guide.pdf --template plain

   Images resolve next to the .md automatically. A missing image becomes a
   visible placeholder — the PDF still builds.

3. Options you actually use:
     --template NAME   `onboarding` (step-per-page, illustrated) or `plain`
                       (general document). List: `md2pdf templates`.
     --var KEY=VALUE   fills a `{{KEY}}` placeholder in the .md; repeatable.
     --assets DIR      only if images live somewhere other than the .md's folder.

4. System libs: WeasyPrint needs Pango/Cairo. On Debian/Ubuntu, once:
     sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0

That's it. Output goes to the -o path (or <input>.pdf). Report the path back.
════════════════════════════════════════════════════════════════════════ -->

# md2pdf

Turn a Markdown file into a clean, print-ready **PDF** — with named page
templates, `{{VAR}}` substitution, and inline images (missing images render a
visible placeholder so the build never fails). One small engine, reused by the
CLI and importable as a library.

## Install / run

The `@main` in the URLs below tracks the latest version. Swap it for `@v1` to
**pin** to a fixed, reproducible release (see [Notes](#notes)).

**One-off, no install** — if you have [`uv`](https://astral.sh/uv), run it straight
from git (uv fetches and caches it for you):

```sh
uvx --from git+https://github.com/MortenGuldager/md2pdf@main md2pdf render guide.md
```

**Daily use (recommended)** — install once and get a plain `md2pdf` command on your
`PATH`, so you never type the long `--from …` line again:

```sh
uv tool install git+https://github.com/MortenGuldager/md2pdf@main
md2pdf render guide.md -o guide.pdf --template plain
```

This is the smart choice for repeated use: unlike a shell alias it also works in
scripts, cron and other tools. Handy follow-ups:

```sh
uv tool upgrade md2pdf      # re-resolve @main to its latest commit
uv tool list                # see what's installed
uv tool uninstall md2pdf    # remove it
```

If `md2pdf` isn't found afterwards, make sure uv's bin dir is on your `PATH`
(`uv tool update-shell`, then restart the shell). The installed package is named
`md2pdf-clean`, but the command it exposes is `md2pdf`.

**Or with pip:**

```sh
pip install git+https://github.com/MortenGuldager/md2pdf@main
md2pdf render guide.md -o guide.pdf
```

WeasyPrint needs system libraries (Pango/Cairo). On Debian/Ubuntu:

```sh
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0
```

## Usage

```sh
md2pdf render INPUT.md [-o OUT.pdf] [-t TEMPLATE] [--var KEY=VALUE] [--assets DIR] [--html]
md2pdf templates            # list available templates
md2pdf render --help
```

- **Images** — reference them with a relative path in the Markdown
  (`![My caption](img/step1.png)`). They resolve against the `.md`'s folder
  (override with `--assets`). The alt-text becomes the figure caption. A missing
  file renders a dashed placeholder instead of erroring.
- **Templates** — `onboarding` (each `##` starts a new page — an illustrated,
  step-per-page guide) and `plain` (a neutral, readable document). Add your own
  by dropping a `NAME.css` into `src/md2pdf/templates/`.
- **Substitution** — any `{{KEY}}` in the Markdown is replaced by
  `--var KEY=value`. Unfilled placeholders are left visible on purpose.
- **Callouts** — a blockquote beginning `NOTE:`, `WARN:` or `TIP:` renders as a
  coloured box.

### Example

`guide.md`:

```markdown
# Kom godt i gang

{{WELCOME}}

## Trin 1
![Login-siden med reset-linket markeret](screenshots/01-reset.png)

> NOTE: Brug dit korte brugernavn, ikke din e-mail.
```

```sh
md2pdf render guide.md -o Kom-godt-i-gang.pdf \
    --template onboarding --var WELCOME="Velkommen til Regnskab."
```

## As a library

```python
from md2pdf import render
pdf_bytes, missing_images, missing_vars = render(
    open("guide.md").read(),
    template="plain",
    vars={"WELCOME": "Velkommen."},
    asset_dir="path/to/guide/folder",
    out_pdf="guide.pdf",
)
```

## Notes

- **`@main` vs `@v1`** — install from `@main` to always get the newest version, or
  pin to `@v1` (a fixed tag) for a reproducible build that won't change under you.
  Either way the package's own dependencies stay version-pinned (below); the ref
  only chooses which snapshot of md2pdf itself you install.
- **Reproducible output** — dependencies are version-pinned so glyphs and layout
  match across machines. For pixel-identical output everywhere, also ensure the
  same fonts are installed (the templates use DejaVu Sans / Liberation with
  common fallbacks).
- **Security** — the renderer's URL fetcher is locked to the asset folder:
  `file://` paths outside it and any `http(s)://` are refused. Safe to reuse
  behind a network endpoint later.

Released into the public domain under the [Unlicense](LICENSE).
