"""A host a widget declares has to be a host the CSP lets it reach.

Every widget's ``widget.toml`` carries ``hosts`` -- "the external hosts this
widget may call" -- and ``Manifest.hosts`` parses it. The browser's permission
to make those calls comes from somewhere else entirely: the
``Content-Security-Policy`` header in
``deploy/roles/nginx/templates/ssl.conf``, whose ``connect-src`` list is
maintained by hand.

The two fell out of step, and the way it showed up is the point. HogSwap
declares ``https://hogswap-v1.liquihog.dev``; ``connect-src`` never named it.
So for a reader whose preferred router was HogSwap, every quote failed with

    Refused to connect because it violates the document's Content Security
    Policy

which is a console message, not an error the page can catch and explain -- the
fetch simply never happens. Nothing in the Python suite, the jest suites or the
functional tests could see it, because none of them serve pages through nginx.

**A wildcard source counts.** Haystack declares
``https://mainnet-api.4160.nodely.dev`` and the policy allows
``https://*.nodely.dev``, which permits it; the matcher below implements that
rather than demanding an exact line per host.

Read `test_a_host_nobody_allowed_is_reported` first: it is what stops a
mistake in the parsing or the matcher from leaving a sweep that permits
everything.
"""

import re
from pathlib import Path

import pytest

from widgethost.registry import discover_manifests

#: website/widgethost/tests/ -> the repository root.
REPOSITORY = Path(__file__).resolve().parents[3]

SSL_CONF = REPOSITORY / "deploy" / "roles" / "nginx" / "templates" / "ssl.conf"


def _connect_src():
    """Return the sources the deployed CSP allows the page to connect to.

    :return: list of str
    """
    directive = re.search(r"connect-src\s+([^;\"]*)", SSL_CONF.read_text())
    return directive.group(1).split() if directive else []


def _permitted(host, sources):
    """Return whether `host` is allowed by any of the CSP `sources`.

    Exact match, or a wildcard source whose scheme agrees and whose domain
    suffix the host ends with -- ``https://*.nodely.dev`` permits
    ``https://mainnet-api.4160.nodely.dev``, and CSP allows more than one
    label in place of the star.

    :param host: scheme-qualified host a widget declares
    :type host: str
    :param sources: CSP connect-src sources
    :type sources: list
    :return: bool
    """
    for source in sources:
        if source == host:
            return True
        scheme, star, suffix = source.partition("://*")
        if not star or not suffix.startswith("."):
            continue
        if host.startswith(f"{scheme}://") and host.endswith(suffix):
            return True
    return False


def _declared_hosts():
    """Return every (widget id, host) pair the manifests declare.

    :return: list of two-tuples
    """
    return [
        (manifest.id, host)
        for _, manifest in discover_manifests()
        for host in manifest.hosts
    ]


class TestDeclaredHostsAreAllowedByTheCsp:
    """The manifest says who it calls; the policy decides whether it may."""

    def test_the_connect_src_directive_was_found(self):
        """Cheap, and it is what makes the sweep below mean anything.

        A `connect-src` this cannot parse returns an empty source list, and
        then the sweep fails for every host with a confusing message instead
        of this one.
        """
        if not SSL_CONF.exists():
            pytest.skip(f"no nginx template at {SSL_CONF}")

        sources = _connect_src()

        assert "'self'" in sources, f"parsed connect-src as {sources}"

    def test_every_declared_host_is_allowed(self):
        if not SSL_CONF.exists():
            pytest.skip(f"no nginx template at {SSL_CONF}")

        sources = _connect_src()
        blocked = {
            f"{widget}: {host}"
            for widget, host in _declared_hosts()
            if not _permitted(host, sources)
        }

        assert not blocked, (
            "these widgets declare hosts the deployed Content-Security-Policy "
            f"does not allow, so the browser will refuse the call: {blocked}. "
            "Add each to connect-src in "
            "deploy/roles/nginx/templates/ssl.conf."
        )

    def test_a_host_nobody_allowed_is_reported(self):
        """The anchor. Without it the matcher could permit anything.

        Checked against a fixed source list rather than the deployed one, so
        it keeps testing the matcher even as the policy changes.
        """
        sources = [
            "'self'",
            "https://api.folksrouter.io",
            "https://*.nodely.dev",
        ]

        assert _permitted("https://api.folksrouter.io", sources)
        assert _permitted("https://mainnet-api.4160.nodely.dev", sources)
        assert _permitted("https://a.nodely.dev", sources)

        assert not _permitted("https://evil.example.com", sources)
        # the scheme is part of the source, and a wildcard does not cross it
        assert not _permitted("http://mainnet-api.4160.nodely.dev", sources)
        # nodely.dev itself is not a subdomain of nodely.dev
        assert not _permitted("https://nodely.dev", sources)
        # a suffix match is not a domain match
        assert not _permitted("https://notnodely.dev", sources)

    def test_the_sweep_has_something_to_sweep(self):
        """`hosts` is optional, so an empty sweep would pass in silence.

        Not an assertion about which widgets exist -- a fork may ship none of
        them -- but if no widget declares a host at all, this module is
        checking nothing and should say so rather than pass.
        """
        declared = _declared_hosts()

        if not declared:
            pytest.skip("no widget declares an external host")

        assert any(host.startswith("https://") for _, host in declared)

    def test_the_hogswap_router_can_reach_its_quote_endpoint(self):
        """The regression, named, so it survives a refactor of the sweep."""
        if not SSL_CONF.exists():
            pytest.skip(f"no nginx template at {SSL_CONF}")

        hosts = [host for widget, host in _declared_hosts() if widget == "hogswap"]
        if not hosts:
            pytest.skip("the hogswap widget is not installed")

        assert "https://hogswap-v1.liquihog.dev" in hosts
        assert _permitted("https://hogswap-v1.liquihog.dev", _connect_src())
