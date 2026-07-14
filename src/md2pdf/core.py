"""Render Markdown to a clean, print-ready PDF.

One engine, reused by the CLI and anything else that imports it. Pipeline:

    markdown text
      -> {{VAR}} substitution        (arbitrary keys from `vars`)
      -> HTML                        (python-markdown: extra, sane_lists, tables)
      -> <img> becomes <figure>      (caption from alt-text; placeholder if missing)
      -> NOTE:/WARN:/TIP: callouts   (coloured boxes)
      -> named CSS template          (A4, page furniture)
      -> PDF                         (WeasyPrint)

Images are resolved relative to `asset_dir` exactly like a folder on disk, so a
Markdown file with `![cap](screenshots/x.png)` next to a `screenshots/` folder
"just works". A missing image renders a visible placeholder instead of failing,
so the PDF always builds.

Security: the WeasyPrint url_fetcher is locked to `asset_dir` — `file://` outside
it and any `http(s)://` are refused. This keeps the same engine safe if it is
ever put behind a network endpoint.
"""
import os
import re
import html as _html
import urllib.parse

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# <img ...> in any attribute order, and its attributes
IMG_RE = re.compile(r"<img\b[^>]*?/?>", re.IGNORECASE)
ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
VAR_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")


def list_templates():
    """Available template names (CSS files in the templates dir), sorted."""
    return sorted(
        f[:-4] for f in os.listdir(TEMPLATES_DIR) if f.endswith(".css")
    )


def load_template(name):
    """CSS for a named template. Raises ValueError with the valid names on miss."""
    path = os.path.join(TEMPLATES_DIR, name + ".css")
    if not os.path.isfile(path):
        raise ValueError(
            f"unknown template {name!r}; available: {', '.join(list_templates())}"
        )
    with open(path, encoding="utf-8") as f:
        return f.read()


def substitute_vars(text, vars):
    """Replace {{KEY}} with vars[KEY]. Unknown keys are left untouched on purpose
    so a forgotten substitution is visible in the output rather than silently
    blanked. Returns (text, sorted list of keys that had no value)."""
    vars = vars or {}
    missing = set()

    def repl(m):
        key = m.group(1)
        if key in vars:
            return str(vars[key])
        missing.add(key)
        return m.group(0)

    return VAR_RE.sub(repl, text), sorted(missing)


def render_images(html_body, asset_dir):
    """Turn each <img> into a <figure> with a caption from its alt-text. If the
    file is missing, draw a labelled placeholder instead so the build never fails.
    Returns (html, number of missing images)."""
    missing = [0]

    def repl(m):
        attrs = dict(ATTR_RE.findall(m.group(0)))
        src = attrs.get("src", "")
        cap = attrs.get("alt", "")
        path = os.path.join(asset_dir, src)
        if src and os.path.isfile(path):
            fig_inner = f'<img src="{_html.escape(src)}" alt="{_html.escape(cap)}" />'
        else:
            missing[0] += 1
            fig_inner = (
                '<div class="placeholder">'
                '<div class="ph-cam">BILLEDE</div>'
                f'<span class="ph-file">{_html.escape(src or "(intet filnavn)")}</span>'
                '<div class="ph-cap">billedet mangler — læg filen ved siden af .md’en, så bygges det ind</div>'
                "</div>"
            )
        caption = f"<figcaption>{_html.escape(cap)}</figcaption>" if cap else ""
        return f"<figure>{fig_inner}{caption}</figure>"

    out = IMG_RE.sub(repl, html_body)
    return out, missing[0]


def tag_callouts(html_body):
    """Give blockquotes a class + tag from a NOTE:/WARN:/TIP: prefix."""
    kinds = {"WARN": "warn", "NOTE": "note", "TIP": "tip"}
    for key, cls in kinds.items():
        html_body = re.sub(
            rf"<blockquote>\s*<p>{key}:\s*",
            f'<blockquote class="{cls}"><p><span class="tag">{key}</span> ',
            html_body,
        )
    return html_body


def _make_url_fetcher(asset_dir):
    """A WeasyPrint url_fetcher locked to asset_dir: allow data: URIs and files
    inside asset_dir, refuse everything else (file:// escapes, http(s), ftp...)."""
    from weasyprint import default_url_fetcher

    root = os.path.realpath(asset_dir)

    def fetch(url, *args, **kwargs):
        if url.startswith("data:"):
            return default_url_fetcher(url, *args, **kwargs)
        if url.startswith("file:"):
            path = os.path.realpath(urllib.parse.unquote(urllib.parse.urlparse(url).path))
            if path == root or path.startswith(root + os.sep):
                return default_url_fetcher(url, *args, **kwargs)
            raise ValueError(f"blocked file outside asset dir: {path}")
        raise ValueError(f"blocked non-local URL: {url}")

    return fetch


def build_html(markdown_text, *, template="onboarding", vars=None, asset_dir="."):
    """Markdown (+vars) -> a full standalone HTML document string.
    Returns (html, missing_images, missing_vars)."""
    import markdown as _markdown

    text, missing_vars = substitute_vars(markdown_text, vars)
    body = _markdown.markdown(text, extensions=["extra", "sane_lists", "tables"])
    body, missing_images = render_images(body, asset_dir)
    body = tag_callouts(body)
    css = load_template(template)
    doc = (
        "<!doctype html><html lang=da><head><meta charset=utf-8>"
        f"<style>{css}</style></head><body>{body}</body></html>"
    )
    return doc, missing_images, missing_vars


def render(markdown_text, *, template="onboarding", vars=None, asset_dir=".",
           out_pdf=None):
    """Render Markdown to PDF. Writes to `out_pdf` if given; always returns the
    PDF bytes. Returns (pdf_bytes, missing_images, missing_vars)."""
    from weasyprint import HTML

    doc, missing_images, missing_vars = build_html(
        markdown_text, template=template, vars=vars, asset_dir=asset_dir
    )
    pdf = HTML(
        string=doc,
        base_url=os.path.realpath(asset_dir),
        url_fetcher=_make_url_fetcher(asset_dir),
    ).write_pdf()
    if out_pdf:
        with open(out_pdf, "wb") as f:
            f.write(pdf)
    return pdf, missing_images, missing_vars
