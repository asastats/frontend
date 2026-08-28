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
    # Not just `is None`: Django resolves a variable that is absent from the
    # context to `string_if_invalid`, which is `""` by default -- so a template
    # rendered before its slot map arrives hands this a string. The historic
    # widget streams each batch of rows as its own websocket message, so the
    # AttributeError that followed took the socket down instead of rendering a
    # row without a colour.
    if not hasattr(mapping, "get"):
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
    :return: type matching the input where possible
    """
    if value is None:
        return 0

    try:
        if isinstance(value, int):
            return abs(value)

        return abs(float(value))

    except (TypeError, ValueError):
        return 0


@register.simple_tag
def dist_price(d, decimals):
    """Per-distribution-entry implied ALGO price.

    Used by ``snippets/asas/program.html`` to render a price line for
    each row inside a program's distribution breakdown. Prior to this
    fix the template reused the parent asaitem's top-level ``price``
    for every row in the loop, so all distribution rows displayed the
    same (wrong) price. This tag computes the price from the specific
    distribution entry's own ``value`` (ALGO) and ``amount`` (raw
    asset units), scoped per-iteration.

    :param d: single distribution dict from ``prog.distribution``;
        must contain ``value`` (ALGO amount, numeric or numeric
        string) and ``amount`` (raw integer asset units, matching the
        same encoding as ``prog.amount`` elsewhere in this template)
    :param decimals: asset.decimals, used to convert the raw integer
        ``amount`` into asset-unit terms
    :return: float price (ALGO per 1 asset unit), or None if the
        entry is missing data, malformed, or amount is zero
    """
    try:
        amount_units = float(d["amount"]) / (10 ** int(decimals))
        if not amount_units:
            return None
        return float(d["value"]) / amount_units
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


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

    ``entity`` is one of ``"address"``, ``"asset"``, ``"transaction"``,
    ``"application"``.

    :param context: the template context (carries the viewer)
    :type context: dict
    :param entity: blockchain entity kind
    :type entity: str
    :param value: address, asset id, transaction id, or application id
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


@register.simple_tag(takes_context=True)
def program_url(context, program_url):
    """Return provided program URL or its failback link in block explorer.

    :param context: the template context (carries the viewer)
    :type context: dict
    :param program_url: fuklly formated URL or an explorer failback
    :type program_url: str
    :var entity: blockchain entity kind
    :type entity: str
    :var prefix: currently processed entity's identifier
    :type prefix: str
    :var value: address or application id
    :type value: str
    :return: str
    """
    if not isinstance(program_url, str):
        return program_url

    for entity in ("address", "application"):
        prefix = f"{entity}="
        if program_url.startswith(prefix):
            value = program_url[len(prefix) :]
            if entity == "application" and not value.isnumeric():
                return program_url

            return explorer_constants.explorer_link(
                _viewer_explorer(context, ""), entity, value
            )

    return program_url


@register.filter
def program_groups(programs):
    """Group an asset's positions by the program holding them, with subtotals.

    The dynamic designs stack positions under their program rather than
    listing them flat, because "how much of this asset is locked in CompX" is
    the question a reader with the same asset in nine places is actually asking,
    and a flat list makes them add it up themselves.

    **By program, not by venue**, and the distinction is not pedantic. The
    payload's ``program.name`` is a venue for most position types -- "AlgoRai
    deposit", "CompX token stream", "Wallet balance" -- but for liquidity
    positions it is the category "Liquidity", with the actual venue in
    ``program.code`` ("Pact LP ALGO-EURS"). So the reference address groups 18
    LP positions across five venues under one "Liquidity" heading. That is a
    useful grouping and an honest one; calling it a venue grouping would not be,
    and splitting `code` on whitespace to recover the venue would be guessing at
    a string the engine never promised the shape of.

    Grouping happens here rather than in the view because it is presentation:
    design 1 renders the same programs ungrouped, and the serialized payload is
    shared with the JSON API, which must not grow a website-shaped key.

    Order is first appearance, not value. The payload arrives ordered by the
    engine, and re-sorting here would put the subtotal ordering at odds with the
    position ordering inside each group for no gain -- the toolbar sorts, later,
    and it sorts both together.

    A position with no program name is its own group under the empty string,
    which the template renders as the asset's own balance rather than inventing
    a label for it.

    :param programs: one asaitem's ``programs`` list
    :type programs: list
    :var groups: program name mapped to its accumulating group
    :type groups: dict
    :return: list of dicts with ``name``, ``url``, ``positions`` and ``total``
    :rtype: list
    """
    groups = {}
    for program in programs or ():
        source = program.get("program") or {}
        name = source.get("name") or ""
        group = groups.setdefault(
            name, {"name": name, "url": source.get("url"), "positions": [], "total": 0}
        )
        group["positions"].append(program)
        try:
            group["total"] += float(program.get("value") or 0)
        except (TypeError, ValueError):
            # A value the engine could not evaluate contributes nothing to the
            # subtotal rather than discarding the whole group's arithmetic.
            pass
    return list(groups.values())


@register.filter
def beyond(rows, shown):
    """Return how many of ``rows`` sit past the first ``shown``.

    Django's ``add`` filter cannot subtract one variable from another, which is
    the whole reason this exists.

    Never negative: a section shorter than its first batch has nothing beyond
    it, and "Show -3 more assets" is worse than showing no control at all.

    :param rows: the section's rows
    :type rows: list
    :param shown: how many are shown before the control
    :type shown: int
    :return: int
    """
    try:
        return max(len(rows) - int(shown), 0)
    except (TypeError, ValueError):
        return 0


@register.filter
def next_batch(rows, shown):
    """Return how many rows the *next* press of "Show more" reveals.

    Both designs reveal one batch per press, and a batch is the same size as the
    first fold -- so this is :func:`beyond` capped at ``shown``.

    Its own filter rather than the tail count, because the tail is what the
    label used to say and it was wrong: "Show 39 more assets" over a control
    that reveals twenty is a promise the control does not keep. The scripts
    already rewrote the label to the batch on the first repaint, so the served
    page was the one screen where the number was false -- which is the screen
    every reader sees first.

    :param rows: the section's rows
    :type rows: list
    :param shown: the batch size, which is also the first fold
    :type shown: int
    :return: int
    """
    try:
        return min(beyond(rows, shown), max(int(shown), 0))
    except (TypeError, ValueError):
        return 0


@register.filter
def holdings_amount(asaitem):
    """Return an asaitem's holding as a plain number, for sorting on.

    The toolbar sorts by Holdings, and the only holding figure on the page is
    ``amount_repr``'s output -- "1,234.5678", grouped for reading. Parsing that
    back in the browser means agreeing with Django's thousands separator
    forever, and the separator is locale-dependent. This emits the same number
    ungrouped, into a data attribute nobody reads.

    Raw ``amount`` cannot be used instead: it is in the asset's base units, so
    an asset with 6 decimals sorts a million places above one with 0 holding
    the same quantity.

    :param asaitem: one entry from account.asaitems
    :type asaitem: dict
    :var decimals: the asset's decimal places
    :type decimals: int
    :return: str
    """
    try:
        decimals = int((asaitem.get("asset") or {}).get("decimals") or 0)
        return repr(int(asaitem.get("amount") or 0) / (10**decimals))
    except (AttributeError, TypeError, ValueError):
        return "0"


def _number(value):
    """Return ``value`` as a float, or 0.0 if it is not one.

    The payload is not uniform -- an asset's value arrives as a float and an
    NFT floor as a decimal string -- and every figure this module renders has
    to survive one that arrived as neither. Module level rather than nested in
    the one filter that first needed it, because three now do and a second copy
    is a second rule.

    :param value: a figure in whatever form the payload carries it
    :return: float
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _collection_totals(collection):
    """Return ``(estimate, floor)`` for one NFT collection, as floats.

    :param collection: one entry from account.nftcollections
    :type collection: dict
    :var floor: summed floor price across the collection's items
    :type floor: float
    :return: tuple of two floats
    """
    floor = 0.0
    for row in (collection or {}).get("nfts") or ():
        prices = ((row or {}).get("nft") or {}).get("floor") or ()
        # A list, because an item can be floored on several marketplaces. The
        # first is the one design 1 reports, so it is the one used here too --
        # differing on which floor is "the" floor would be a worse divergence
        # than either choice.
        if prices:
            floor += _number(prices[0].get("price"))
    return _number((collection or {}).get("value")), floor


@register.filter
def collection_floor(collection):
    """Return a collection's summed floor price.

    The estimate is what the section totals; the floor is what a marketplace
    will pay for the same items today, and the gap between them is the only
    fact about a collection that one figure cannot express. Summed here rather
    than in the template because Django cannot add a list of nested values.

    An item nobody floors contributes nothing, which is right: a floor of zero
    and no floor at all are the same amount of money. The card says which it is
    with a chip, not with the number.

    :param collection: one entry from account.nftcollections
    :type collection: dict
    :return: float
    """
    return _collection_totals(collection)[1]


@register.filter
def collection_above_floor(collection):
    """Return how much of a collection's estimate sits above its floor.

    The second half of the two-part bar. Never negative -- an estimate below
    the floor would draw a bar backwards -- and never quite zero, because a
    flex basis of 0 collapses the whole bar rather than showing one full side.

    :param collection: one entry from account.nftcollections
    :type collection: dict
    :var estimate: the collection's estimated value
    :type estimate: float
    :var floor: the collection's summed floor
    :type floor: float
    :return: float
    """
    estimate, floor = _collection_totals(collection)
    return max(estimate - floor, 0.001)


@register.filter
def clears_floor(row):
    """Return True if an NFT's estimate reaches the floor it is priced against.

    A filter rather than a template comparison, because both figures arrive as
    decimal *strings* and ``{% if a > b %}`` compares those lexically: "215.98"
    sorts below "25.00", so the reference address would have read "the estimate
    does not clear it" on an item worth eight times its floor.

    An item with no floor clears nothing, and the template renders a different
    line for that case rather than asking this.

    :param row: one entry from a collection's ``nfts``
    :type row: dict
    :var floors: the item's floor prices, one per marketplace
    :type floors: list
    :return: bool
    """
    floors = ((row or {}).get("nft") or {}).get("floor") or ()
    if not floors:
        return False
    return _number((row or {}).get("price")) >= _number(floors[0].get("price"))


@register.filter
def beats_last_purchase(nft):
    """Return True if an NFT's best purchase price exceeds its most recent one.

    Both are the same transaction for most items, and showing the pair twice
    says nothing. Worth showing when they differ, because a best price well
    above the last one is the item's own history telling the reader what it has
    been worth.

    A filter for the same reason as :func:`clears_floor`: the prices are decimal
    strings, and ``{% if a > b %}`` compares them lexically -- "9.5" beats
    "210.0". Design 1 makes that comparison in the template and this design does
    not, which is a deliberate divergence rather than drift: the answer there is
    sometimes wrong, and design 1 is finished and not to be edited.

    :param nft: one ``row.nft`` from a collection
    :type nft: dict
    :return: bool
    """
    best = (nft or {}).get("max_purchase") or {}
    last = (nft or {}).get("last_purchase") or {}
    if not best:
        return False
    return _number(best.get("price")) > _number(last.get("price"))


@register.filter
def collection_tile(name):
    """Return the short label for a collection's tile.

    A collection has no logo of its own, so the tile carries initials the way a
    monospaced avatar does. Four characters is what fits the 38px tile at the
    prototype's type size; longer names are cut rather than scaled, because
    shrinking the type to fit makes some tiles unreadable and the rest
    inconsistent.

    Word initials when a name has several words -- "Brave New World" gives
    "BNW", which a reader recognises -- and the leading characters otherwise.

    :param name: the collection's name
    :type name: str
    :var words: the name's whitespace-separated parts
    :type words: list
    :return: str
    """
    words = str(name or "").split()
    if not words:
        return "?"
    if len(words) > 1:
        return "".join(word[0] for word in words[:4]).upper()
    return words[0][:4].upper()


@register.filter
def position_band(program):
    """Return the allocation category one position belongs to.

    The band above the list is a decomposition of the same positions the list
    shows, so the toolbar's category filter has to agree with it exactly: a
    reader who presses "Staked" and sees a balance row has been told the band
    was lying. That means the category has to be known *per position*, and the
    payload does not carry one -- :class:`utils.structs.Consolidated` arrives
    already summed.

    The rule is therefore reproduced here, and it is reproduced rather than
    shared because the four originals in :mod:`utils.charts` --
    ``_balance_totals_from_serialized_data`` and its three siblings -- are
    dict comprehensions over the whole payload with no per-position function to
    call. Extracting one would mean editing the module design 1's charts are
    built from, which is finished and is not to be touched.

    Reproduction invites drift, so it is *tested* rather than commented:
    ``test_dynamic_extras.py`` sums the reference payload's positions by this
    filter and asserts the four totals equal ``Consolidated``'s own. If either
    side ever changes, that fails.

    One deliberate difference, and it is not drift. ``_balance_totals`` uses
    ``next(...)``, so a second ``Balance`` position on the same asset
    contributes nothing to the balance total; the ``defi`` comprehension
    excludes every ``Balance`` position, so that second one lands in no
    category at all and is missing from the band. Here it is labelled
    ``balance``, because a row on the page must belong to the category a reader
    would say it belongs to. The reference payload has no such asset, which is
    why the two agree; if one appears, the band under-reports and this filter
    is right.

    :param program: one entry from an asaitem's ``programs``
    :type program: dict
    :var detail: the position's ``program`` sub-dict
    :type detail: dict
    :var kind: the position's type, e.g. "Balance", "Staked", "Added"
    :type kind: str
    :var name: the position's program name, e.g. "Liquidity", "AlgoRai farm"
    :type name: str
    :return: one of "balance", "staked", "liquidity", "defi"
    :rtype: str
    """
    detail = (program or {}).get("program") or {}
    kind = detail.get("type") or ""
    name = detail.get("name") or ""

    if kind == "Balance":
        return "balance"
    if kind == "Staked" and "farm" not in name:
        return "staked"
    if kind == "Added" and name == "Liquidity":
        return "liquidity"
    return "defi"


#: The allocation categories, in the order the band draws them. The keys match
#: the ``--c-*`` custom properties and the ``.cat-*`` classes in ``input.css``,
#: and the order matches ``utils.structs.Consolidated`` so the two cannot drift.
ALLOCATION_BANDS = (
    ("balance", "Balance"),
    ("staked", "Staked"),
    ("liquidity", "Liquidity"),
    ("defi", "DeFi"),
    ("nft", "NFT"),
)


@register.filter
def allocation_bands(consolidated, total):
    """Return the five allocation categories with their values and shares.

    The "where the money is" band, the category figures beside it and the ratio
    donut are three drawings of one set of numbers, so they are computed once
    here rather than three times in the template. A reader who sees the band and
    the figures disagree has no way to tell which one lied.

    ``consolidated`` supplies four categories and ``total`` the fifth: NFTs are
    valued separately from the programs, so
    :class:`utils.structs.Consolidated`'s last field is the NFT *floor*, not the
    NFT holding, and using it here would quietly under-report.

    Shares are of the categories' own sum rather than of ``total.total``. The
    band is a decomposition and its segments have to reach the full width; a
    rounding gap at the right-hand end reads as missing money.

    :param consolidated: consolidated totals
    :type consolidated: :class:`utils.structs.Consolidated`
    :param total: account totals
    :type total: :class:`utils.structs.Total`
    :var values: category key mapped to its value
    :type values: dict
    :var summed: the categories' own sum, the denominator for every share
    :type summed: float
    :return: list of dicts with ``key``, ``label``, ``value`` and ``share``
    :rtype: list
    """
    if consolidated is None:
        return []

    def _field(source, name):
        """Read ``name`` off a namedtuple *or* a dict.

        The two arguments arrive in different shapes and always have:
        ``consolidated`` is a :class:`utils.structs.Consolidated` namedtuple
        built by the view, while ``total`` is ``account.total`` -- a plain dict
        straight out of the serialized payload. Reading both with ``getattr``
        silently returned 0 for every NFT holding, and the band drew four
        categories summing to 100% while omitting what was, on the reference
        address, the largest one.
        """
        if isinstance(source, dict):
            return _number(source.get(name, 0))
        return _number(getattr(source, name, 0))

    values = {
        "balance": _field(consolidated, "balance"),
        "staked": _field(consolidated, "staked"),
        "liquidity": _field(consolidated, "liquidity"),
        "defi": _field(consolidated, "defi"),
        "nft": _field(total, "nft"),
    }
    # Magnitude, not the signed value: a borrowed position is a negative number
    # and a band cannot be drawn a negative width. It still belongs in the
    # picture, so it contributes its size and keeps its sign in the figure.
    summed = sum(abs(value) for value in values.values())
    return [
        {
            "key": key,
            "label": label,
            "value": values[key],
            "share": (abs(values[key]) / summed * 100) if summed else 0,
        }
        for key, label in ALLOCATION_BANDS
    ]
