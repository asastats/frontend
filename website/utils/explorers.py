"""Module containing constants for blockchain explorer link providers.

:data:`EXPLORERS` maps an explorer key to its display name, base URL and
per-entity path templates. Adding an entry makes the explorer selectable on
the settings page with no further code change.

The engine has no copy of the table: it sends ``"{entity}={value}"`` markers,
resolved here by :func:`marker_link`.
"""

from urllib.parse import quote

from utils.constants.core import DEFAULT_EXPLORER, EXPLORERS

#: Entities the engine may send as an ``"{entity}={value}"`` marker in place of
#: a URL. The ids in the first two must be numeric.
MARKER_ENTITIES = ("application", "asset", "address", "transaction", "group")


def normalized_explorer(explorer):
    """Return ``explorer`` if it is a known key, otherwise the default key.

    :param explorer: candidate explorer key (may be empty/unknown/None)
    :type explorer: str
    :return: a key guaranteed to exist in :data:`EXPLORERS`
    :rtype: str
    """
    return explorer if explorer in EXPLORERS else DEFAULT_EXPLORER


def explorer_choices():
    """Return ``(key, name)`` pairs for a selection widget, default first.

    :var default: the default explorer's ``(key, name)`` pair
    :type default: tuple
    :var others: remaining explorers sorted by display name
    :type others: list
    :return: list of two-tuples
    :rtype: list
    """
    default = (DEFAULT_EXPLORER, EXPLORERS[DEFAULT_EXPLORER]["name"])
    others = sorted(
        (key, conf["name"]) for key, conf in EXPLORERS.items() if key != DEFAULT_EXPLORER
    )
    return [default, *others]


def explorer_name(explorer):
    """Return the display name for ``explorer`` (default's name if unknown).

    :param explorer: explorer key
    :type explorer: str
    :return: str
    """
    return EXPLORERS[normalized_explorer(explorer)]["name"]


def explorer_base(explorer):
    """Return the trailing-slash base URL for ``explorer``.

    Used by callers that need only the provider root (e.g. the ALGO/native
    entry that links to the explorer home rather than a specific asset).

    :param explorer: explorer key
    :type explorer: str
    :return: str
    """
    return EXPLORERS[normalized_explorer(explorer)]["base"]


def explorer_path(explorer, entity):
    """Return the bare path segment for ``entity`` (template minus ``{value}``).

    For example, ``explorer_path("allo", "transaction")`` is ``"tx/"`` and the
    same for Lora is ``"transaction/"``. Used to hand the swap controller a
    provider-agnostic transaction path via a data attribute.

    :param explorer: explorer key
    :type explorer: str
    :param entity: one of ``"address"``, ``"asset"``, ``"transaction"``
    :type entity: str
    :return: str
    """
    conf = EXPLORERS[normalized_explorer(explorer)]
    return conf.get(entity, "").replace("{value}", "")


def explorer_link(explorer, entity, value):
    """Return the full explorer URL for ``entity``

    (``address``/``asset``/``transaction``/``application``).

    Falls back to the default explorer for an unknown key. An unknown ``entity``
    yields the bare base URL rather than raising, so a template typo degrades to
    a still-valid link.

    :param explorer: explorer key
    :type explorer: str
    :param entity: one of ``"address"``, ``"asset"``, ``"transaction"``
    :type entity: str
    :param value: address, asset id, transaction id, or application id to embed
    :return: str
    """
    conf = EXPLORERS[normalized_explorer(explorer)]
    template = conf.get(entity)
    if template is None:
        return conf["base"]
    return conf["base"] + template.format(value=value, quoted=quote(str(value), safe=""))


def parse_marker(link):
    """Return ``(entity, value)`` for an engine explorer marker, else None.

    :param link: URL or ``"{entity}={value}"`` marker
    :type link: str
    :return: tuple or None
    """
    if not isinstance(link, str):
        return None

    for entity in MARKER_ENTITIES:
        prefix = f"{entity}="
        if link.startswith(prefix):
            value = link[len(prefix) :]
            if entity in ("application", "asset") and not value.isnumeric():
                return None
            return entity, value

    return None


def marker_link(explorer, link):
    """Return ``link`` resolved against ``explorer`` if it is a marker.

    An explorer without a page for the entity falls back to the default one:
    Lora and Algo Surf address a group by block round, which markers lack.

    :param explorer: explorer key
    :type explorer: str
    :param link: URL or ``"{entity}={value}"`` marker
    :type link: str
    :return: str
    """
    parsed = parse_marker(link)
    if parsed is None:
        return link

    entity, value = parsed
    if entity not in EXPLORERS[normalized_explorer(explorer)]:
        explorer = DEFAULT_EXPLORER
    return explorer_link(explorer, entity, value)


def is_escrow_marker(link):
    """Return True if ``link`` points at where an abandoned market holds an NFT.

    :param link: URL or ``"{entity}={value}"`` marker
    :type link: str
    :return: bool
    """
    parsed = parse_marker(link)
    return parsed is not None and parsed[0] in ("application", "asset", "address")
