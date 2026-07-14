"""md2pdf — clean Markdown-to-PDF with named templates, {{VAR}} substitution and images."""
from .core import (
    build_html,
    list_templates,
    load_template,
    render,
)

__all__ = ["render", "build_html", "list_templates", "load_template"]
__version__ = "1.0.0"
