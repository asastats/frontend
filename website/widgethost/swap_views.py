"""Router-agnostic base views shared by every inhouse swap-router widget.

Each router widget (folks, haystack, ...) subclasses these and sets only
``template_name`` + ``manifest`` (and, for the shell, ``client_cfg_context``).
The holdings/asset endpoints are generic (account:holdings / assets:lookup); the
only per-router differences are the templates and the shell's non-secret client
config.
"""

import json

from api.client import fetch_account_holdings, fetch_asset_matches
from api.widgets import bundle_and_addresses_from_path
from django.views.generic.base import TemplateView
from walletauth.gating import is_linked_to_user, linked_addresses_for_user
from widgethost.enforcement import WidgetAccessMixin


def safe_json_for_script(value):
    """``json.dumps`` escaped so it cannot break out of a ``<script>`` block.

    Audit finding F1: holdings carry attacker-mintable ASA name/unit, and
    ``json.dumps`` does not escape ``<``/``>``/``&``. These are valid JSON
    escapes that ``JSON.parse`` restores, so there is no behaviour change.

    :param value: any JSON-serialisable object
    :return: a JSON string safe to embed in an HTML ``<script>`` element
    :rtype: str
    """
    return (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


class BaseSwapShellView(WidgetAccessMixin, TemplateView):
    """Render a router widget's swap shell for an address or bundle page.

    :var manifest: this widget's parsed manifest (set by the subclass)
    :type manifest: :class:`widgethost.manifest.Manifest`
    :var bundle: hash made from public Algorand address(es)
    :type bundle: str
    :var addresses: space separated collection of public Algorand addresses
    :type addresses: str
    """

    manifest = None
    bundle = None
    addresses = None

    def client_cfg_context(self):
        """Per-router non-secret client config for the shell. Override.

        :return: dict
        """
        return {}

    def get_context_data(self, *args, **kwargs):
        """Expose bundle, addresses, linked subset, router id + client config.

        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        context["bundle"] = self.bundle
        context["addresses"] = self.addresses
        linked = linked_addresses_for_user(self.request.user, self.addresses.split(" "))
        context["linked_addresses"] = sorted(linked)
        context["router_id"] = self.manifest.id
        context.update(self.client_cfg_context())
        return context

    def test_func(self):
        """Resolve bundle/addresses from the URL and apply the permission gate.

        :return: Boolean
        """
        url_path = self.args[0].upper()
        self.bundle, self.addresses = bundle_and_addresses_from_path(
            url_path, force_bundle=True
        )
        return self.manifest_test_func(len(self.addresses.split(" ")))


class BaseSwapHoldingsView(WidgetAccessMixin, TemplateView):
    """htmx partial: fresh holdings for one linked address via account:holdings.

    Gated to the user's own (linked) address. Emits an F1-safe JSON island.

    :var manifest: this widget's parsed manifest
    :type manifest: :class:`widgethost.manifest.Manifest`
    :var address: the linked Algorand address whose holdings are fetched
    :type address: str
    """

    manifest = None
    address = None

    def get_context_data(self, *args, **kwargs):
        """Fetch and flatten the address' holdings for the panel.

        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        data = fetch_account_holdings(self.address, self.manifest.engine_endpoints)
        holdings = [
            dict(meta, id=int(asset_id))
            for asset_id, meta in sorted(data.items(), key=lambda kv: int(kv[0]))
        ]
        context["address"] = self.address
        context["holdings"] = holdings
        context["holdings_json"] = safe_json_for_script(holdings)
        context["router_id"] = self.manifest.id
        return context

    def test_func(self):
        """Resolve the address and gate on permission plus user-linkage.

        :return: Boolean
        """
        self.address = self.args[0].upper()
        return self.manifest_test_func(1) and is_linked_to_user(
            self.request.user, self.address
        )


class BaseSwapAssetsView(WidgetAccessMixin, TemplateView):
    """htmx partial: ranked asset metadata for a query via assets:lookup.

    :var manifest: this widget's parsed manifest
    :type manifest: :class:`widgethost.manifest.Manifest`
    """

    manifest = None

    def get_context_data(self, *args, **kwargs):
        """Look up assets by name/unit/id for the ``q`` query parameter.

        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["assets"] = (
            fetch_asset_matches(query, self.manifest.engine_endpoints) if query else []
        )
        return context

    def test_func(self):
        """Gate on an authenticated profile (asset metadata is public).

        :return: Boolean
        """
        return self.manifest_test_func(1)
