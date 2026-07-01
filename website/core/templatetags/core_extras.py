"""Module containing Django templates filters and tags for the website."""

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template import Library
from django.template.defaultfilters import floatformat

from core.exportpermissions import tier_allows
from utils import explorers as explorer_constants
from utils.constants.charts import PIE_CHART_MAXIMUM_ITEMS
from utils.constants.core import DEFAULT_EXPLORER, ELEMENTS_STYLING, USDC_ID
from utils.helpers import bundle_from_addresses

register = Library()


@register.filter
def dict_get(mapping, key):
    """Return value from dict-like ``mapping`` for given ``key``.

    Replaces the legacy ``dict_value`` filter. Used for color-slot lookups
    keyed by asset id, where Django's dotted access doesn't reach
    (numeric keys aren't valid attribute names).

    :param mapping: dict to look up in
    :type mapping: dict
    :param key: lookup key
    :return: value at key, or empty string if missing
    """
    if mapping is None:
        return ""
    return mapping.get(key, "")


@register.filter
def asa_icon(asaitem):
    """Return the absolute CDN path to the icon for an asaitem.

    For non-USDC assets, look for a provider override match in three places
    (in order): explicit provider name on any program, the asset's display
    name, and linked URLs on programs. The redundancy matches how the
    serialized payload describes Lofty/ANote assets — some entries carry
    the provider explicitly, some only the linked URL, some only the asset
    name prefix. Falls back to the standard per-asset thumbnail path.

    :param asaitem: serialized asaitem
    :type asaitem: dict
    :return: str
    """
    asset = asaitem.get("asset") or {}
    asset_id = asset.get("id")
    base_url = settings.BASE_CDN_URL.rstrip("/")

    if asset_id != USDC_ID:
        signals = []
        asset_name = asset.get("name") or ""
        signals.append(asset_name)
        for program_entry in asaitem.get("programs") or []:
            program = program_entry.get("program") or {}
            provider = program.get("provider") or {}
            signals.append(provider.get("name") or "")
            for ld in program_entry.get("linked") or []:
                signals.append(ld.get("link") or "")

        blob = " ".join(signals).lower()
        if "lofty" in blob:
            return f"{base_url}/icons/providers/lofty.png"
        if "anote" in blob or "anmc" in (asset.get("unit") or "").lower():
            return f"{base_url}/icons/providers/anote.png"

    return f"{base_url}/icons/{asset_id}t.png"


@register.filter
def provider_icon(name):
    """Return the absolute CDN path to a provider's small icon.

    The existing convention is ``/icons/providers/<name>.png`` where
    ``<name>`` is the lowercased provider name with whitespace stripped.
    This matches the legacy ``coinmarketcap.png`` / ``livecoinwatch.png``
    naming derived by hand in the old templates.

    :param name: provider display name from the serialized payload
    :type name: str
    :return: str
    """
    base_url = settings.BASE_CDN_URL.rstrip("/")
    if not name:
        return ""

    return f"{base_url}/icons/providers/{''.join(name.lower().split())}.png"


@register.filter
def program_url_title(program):
    """Return the anchor title text for a per-program link.

    Centralises the legacy ``"Go to <provider> application"`` boilerplate
    that the old templates inlined into every per-key branch.

    :param program: serialized program object (``asaitem.programs[i].program``)
    :type program: dict
    :return: str
    """
    name = (
        (program or {}).get("provider", {}).get("name")
        or (program or {}).get("name")
        or "provider"
    )
    return f"Go to {name} application"


@register.filter
def bundle_hash(collection):
    """Return bundle hash from provided addresses collection.

    :param collection: collection of public Algorand addresses
    :type collection: list
    :return: str
    """
    return bundle_from_addresses(" ".join(collection))


@register.filter
def dist_height(distchart, max_size=475, min_size=80):
    """Return distribution chart canvas height based on provided object size.

    :param distchart: distribution chart data
    :type distchart: dict
    :param max_size: maximum canvas size
    :type max_size: int
    :param min_size: minimum canvas size
    :type min_size: int
    :return: int
    """
    size = len(distchart.get("labels", []))
    if size < 2:
        return min_size

    elif size > PIE_CHART_MAXIMUM_ITEMS - 2:
        return max_size

    return min_size + int((size - 1) * (max_size - min_size) / PIE_CHART_MAXIMUM_ITEMS)


@register.filter
def historic_access(profile, size):
    """Return True if provided ``profile`` can access historic widget for ``size``.

    :param profile: user profile instance
    :type profile: class:`core.models.Profile`
    :param size: number of Algorand addresses
    :type size: int
    :return: Boolean
    """
    return profile.can_access_historic_widget(size) if profile is not None else False


@register.filter
def historic_data(collection):
    """Return historic widget URL suffix and bundle length from provided arguments.

    :param collection: collection of Algorand addresses
    :type collection: list
    :return: two-tuple
    """
    return bundle_hash(collection), len(collection)


@register.filter
def integer_comma(value):
    """Return provided integer ``value`` to string with thousand separators.

    :param value: value to format
    :type value: int
    :return: string
    """
    return intcomma(value)


@register.filter
def list_item(collection, index):
    """Return value from list at provided index.

    :param collection: collection of items
    :type collection: list
    :param index: index in list to fetch value for
    :type index: int
    :return: int/str
    """
    return collection[index] if index < len(collection) else ""


@register.filter
def amount_repr(amount, decimals):
    """Return amount divided with ten on provided decimals.

    :param amount: asset amount
    :type amount: int
    :param decimals: number of decimal places
    :type decimals: int
    :return: string
    """
    try:
        return floatformat(int(amount) / (10 ** int(decimals)), f"-{decimals}g")
    except (ValueError, TypeError):
        return "0"


@register.filter
def is_distribution(name):
    """Return True if provided name represents a distributed pool.

    :param name: pool name
    :type name: str
    :return: Boolean
    """
    split = name.split("-")
    return len(split) == 2 and split[0] == split[1]


@register.filter
def short_address(address):
    """Return short representation of provided address.

    :param address: Algorand address
    :type address: str
    :return: str
    """
    return address[:5] + "..." + address[-5:]


@register.filter
def short_addresses(addresses):
    """Return short representation of provided addresses.

    :param addresses: Algorand addresses separated by space
    :type addresses: str
    :return: str
    """
    return "\n".join(
        address[:5] + "..." + address[-5:] for address in addresses.split(" ")
    )


@register.filter
def split_by_space(addresses):
    """Return collection of addresses from space-separated ``addresses``.

    :param addresses: Algorand addresses separated by space
    :type addresses: str
    :return: list
    """
    return addresses.split(" ")


@register.filter
def strid(prefix, number):
    """Return string created from provided string prefix and integer.

    :param prefix: prefix of the future string
    :type prefix: str
    :param number: integer part of the future string
    :type number: int
    :return: string
    """
    return "{}{}".format(prefix, number)


@register.filter
def get_styling(elem, key):
    """Return style for the argument.

    :param elem: field element
    :type elem: dictionary
    :param key: key to look for
    :type key: string
    :return: type/style for provided key
    """
    return ELEMENTS_STYLING.get(elem, {}).get(key, "")


@register.filter
def has_styling(elem):
    """Return True if there's styling for element.

    :param elem: field element
    :type elem: dict
    :return: Boolean
    """
    return ELEMENTS_STYLING.get(elem, False)


@register.filter
def invert_price(price):
    """Return 1/price (or 0 when price is missing/zero).

    Used by the per-distribution price line in ``snippets/asas/program.html``
    (Phase 5c-fixes / W3). ``price`` is the parent asaitem's ``price`` field
    — ALGO per 1 unit of asset. Inverting it gives asset units per 1 ALGO,
    which is the form the website renders (e.g. ``0.10966392 USDC/ALGO``).

    :param price: Decimal/string/float price value
    :return: 1/price as a float, or 0.0 if price is falsy or non-numeric
    """
    if not price:
        return 0.0
    try:
        p = float(price)
    except (TypeError, ValueError):
        return 0.0
    if p == 0:
        return 0.0
    return 1.0 / p


@register.filter
def is_negative(value):
    """Return True if ``value`` parses as a strictly negative number.

    Used by ``snippets/asas/program.html`` to detect borrow / debt /
    loss programs whose ``prog.value`` and ``prog.amount`` come back
    negative from the V2 serializer. The template wraps such values
    in parens and applies the ``myred-text`` CSS class.

    :param value: numeric value as int, float, Decimal, or string
    :return: True if value < 0, False otherwise (including unparseable)
    """
    if value is None:
        return False
    try:
        return float(value) < 0
    except (TypeError, ValueError):
        return False


@register.filter
def abs_value(value):
    """Return the absolute value of ``value``, or 0 if unparseable.

    Used by ``snippets/asas/program.html`` to display the magnitude of
    negative amounts (e.g. borrowed asset amount) inside parens without
    a stray minus sign — the parens + ``myred-text`` styling already
    convey the negative semantics.

    For int input returns an int (so it composes cleanly with
    ``amount_repr`` which expects ``int(amount) / 10**decimals``);
    for non-int input returns a float.

    :param value: numeric value as int, float, Decimal, or string
    :return: |value|, type matching the input where possible
    """
    if value is None:
        return 0
    try:
        if isinstance(value, int):
            return abs(value)
        return abs(float(value))
    except (TypeError, ValueError):
        return 0


@register.filter
def export_access(profile, size):
    """Gate B: may this browsing user export a bundle of ``size``?"""
    return tier_allows(profile.permission, size) if profile is not None else False


@register.filter
def export_capability(deployment_permission, size):
    """Gate A: is this deployment entitled to export a bundle of ``size``?"""
    return tier_allows(deployment_permission, size)


# # EXPLORERS
def _viewer_explorer(context, override=""):
    """Resolve the explorer key to use for the current render.

    Resolution order, first hit wins: an explicit ``override`` argument; a
    ``preferred_explorer`` value placed directly in the template context (used
    by the historic widget, which renders over a WebSocket with no ``request``);
    the authenticated viewer's saved preference; otherwise the default. Anonymous
    or unauthenticated viewers always get the default, so public pages keep
    showing Allo.

    :param context: the template context
    :type context: dict
    :param override: explicit explorer key, if a caller wants to force one
    :type override: str
    :return: a key guaranteed to exist in the explorer registry
    :rtype: str
    """
    if override:
        return explorer_constants.normalized_explorer(override)

    explicit = context.get("preferred_explorer")
    if explicit:
        return explorer_constants.normalized_explorer(explicit)

    request = context.get("request")
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        profile = getattr(user, "profile", None)
        if profile is not None:
            return profile.preferred_explorer_or_default()

    return DEFAULT_EXPLORER


@register.simple_tag(takes_context=True)
def explorer_url(context, entity, value, explorer=""):
    """Return the viewer's explorer URL for ``entity`` and ``value``.

    Replaces the hard-coded ``https://allo.info/...`` anchors. ``entity`` is one
    of ``"address"``, ``"asset"``, ``"transaction"``.

    :param context: the template context (carries the viewer)
    :type context: dict
    :param entity: blockchain entity kind
    :type entity: str
    :param value: address, asset id, or transaction id
    :param explorer: optional explicit explorer key override
    :type explorer: str
    :return: str
    """
    return explorer_constants.explorer_link(
        _viewer_explorer(context, explorer), entity, value
    )


@register.simple_tag(takes_context=True)
def explorer_base(context, explorer=""):
    """Return the viewer's explorer base URL (provider home).

    Used for the native-ALGO / bundle cases that link to the explorer root
    instead of a specific entity.

    :param context: the template context
    :type context: dict
    :param explorer: optional explicit explorer key override
    :type explorer: str
    :return: str
    """
    return explorer_constants.explorer_base(_viewer_explorer(context, explorer))


@register.simple_tag(takes_context=True)
def explorer_name(context, explorer=""):
    """Return the viewer's explorer display name (e.g. ``"Allo"``).

    :param context: the template context
    :type context: dict
    :param explorer: optional explicit explorer key override
    :type explorer: str
    :return: str
    """
    return explorer_constants.explorer_name(_viewer_explorer(context, explorer))


@register.simple_tag(takes_context=True)
def explorer_tx_path(context, explorer=""):
    """Return the viewer's explorer transaction path segment (e.g. ``"tx/"``).

    Handed to the swap controller via a data attribute so the success link
    follows the viewer's chosen explorer.

    :param context: the template context
    :type context: dict
    :param explorer: optional explicit explorer key override
    :type explorer: str
    :return: str
    """
    return explorer_constants.explorer_path(
        _viewer_explorer(context, explorer), "transaction"
    )
