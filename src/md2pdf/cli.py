"""md2pdf command-line interface.

    md2pdf render guide.md -o out.pdf --template onboarding --var NAME=Regnskab
    md2pdf templates          # list available templates

Images are resolved next to the .md by default (override with --assets), so a
folder of `guide.md` + `screenshots/*.png` renders as-is.
"""
import argparse
import os
import sys

from . import core


def _parse_vars(pairs):
    """--var KEY=VALUE ... -> {KEY: VALUE}. Keys are upper-cased to match {{KEY}}."""
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"error: --var must be KEY=VALUE, got {p!r}")
        key, val = p.split("=", 1)
        out[key.strip().upper()] = val
    return out


def _cmd_render(args):
    src = os.path.abspath(args.input)
    if not os.path.isfile(src):
        sys.exit(f"error: no such file: {args.input}")
    with open(src, encoding="utf-8") as f:
        text = f.read()

    asset_dir = os.path.abspath(args.assets) if args.assets else os.path.dirname(src)
    out_pdf = os.path.abspath(args.out) if args.out else os.path.splitext(src)[0] + ".pdf"
    vars = _parse_vars(args.var)

    try:
        _pdf, missing_images, missing_vars = core.render(
            text, template=args.template, vars=vars,
            asset_dir=asset_dir, out_pdf=out_pdf,
        )
    except ValueError as e:  # unknown template, blocked URL, ...
        sys.exit(f"error: {e}")

    if args.html:
        doc, _, _ = core.build_html(
            text, template=args.template, vars=vars, asset_dir=asset_dir
        )
        html_out = os.path.splitext(out_pdf)[0] + ".html"
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"wrote {html_out}")

    note = []
    if missing_images:
        note.append(f"{missing_images} image(s) still missing")
    if missing_vars:
        note.append(f"unfilled var(s): {', '.join('{{%s}}' % v for v in missing_vars)}")
    print(f"wrote {out_pdf}" + (f"  ({'; '.join(note)})" if note else "  (all assets in place)"))


def _cmd_templates(args):
    for name in core.list_templates():
        print(name)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="md2pdf",
        description="Render a Markdown file to a clean, print-ready PDF.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="render a .md file to .pdf")
    r.add_argument("input", help="path to the Markdown file")
    r.add_argument("-o", "--out", help="output PDF path (default: <input>.pdf)")
    r.add_argument("-t", "--template", default="onboarding",
                   help="template name (see `md2pdf templates`; default: onboarding)")
    r.add_argument("--var", action="append", metavar="KEY=VALUE",
                   help="fill a {{KEY}} placeholder; repeatable")
    r.add_argument("--assets", metavar="DIR",
                   help="folder images are resolved against (default: the .md's folder)")
    r.add_argument("--html", action="store_true",
                   help="also write the intermediate .html (for browser print)")
    r.set_defaults(func=_cmd_render)

    t = sub.add_parser("templates", help="list available templates")
    t.set_defaults(func=_cmd_templates)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
