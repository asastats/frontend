"""Render the error pages nginx serves as files into plain HTML.

nginx's `error_page` locations point at the output directory (deploy role
`nginx`, `site_server_block.conf`). See docs/logbook.md.

Usage::

    python manage.py rendererrorpages
    python manage.py rendererrorpages --output /tmp/errorpages
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader

#: The pages nginx serves itself; names must match `site_server_block.conf`.
NGINX_ERROR_PAGES = ("404.html", "403_csrf.html", "500.html", "503r.html")


class Command(BaseCommand):
    help = "Render the error pages nginx serves into plain HTML files."

    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=Path,
            default=settings.ERROR_PAGES_ROOT,
            help="directory to write into (default: settings.ERROR_PAGES_ROOT)",
        )

    def handle(self, *args, **options):
        output = options["output"]
        output.mkdir(parents=True, exist_ok=True)
        # The same context custom_server_error gives 500.html: no request.
        context = {"WEBSITE_URL": settings.WEBSITE_URL}
        written = 0
        for name in NGINX_ERROR_PAGES:
            html = loader.get_template(name).render(context)
            target = output / name
            if target.exists() and target.read_text() == html:
                continue
            temporary = target.with_suffix(".tmp")
            temporary.write_text(html)
            temporary.chmod(0o644)  # nginx reads it, whatever the umask
            temporary.replace(target)
            written += 1
        # The deploy's changed_when reads this line.
        self.stdout.write(f"{written} error pages written to {output}")
