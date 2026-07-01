"""Module containing constants for blockchain explorer link providers.

A single registry (:data:`EXPLORERS`) maps an explorer key to its display name,
base URL, and per-entity path templates. Allo is the default and the historical
hard-coded provider; adding an entry here makes the explorer selectable on the
user settings page with no further code change, mirroring how a swap-router
widget becomes selectable just by being discovered.

The same table is intentionally duplicated on the backend (``engine``) so the
closed-source group/transaction link builder can resolve a URL without importing
frontend code -- the same one-way, no-shared-import arrangement already used for
``SUBSCRIPTION_TIER_PERMISSIONS``.
"""

DEFAULT_EXPLORER = "allo"

# Per explorer: ``name`` (rendered label), ``base`` (trailing-slash URL), and
# ``address`` / ``asset`` / ``transaction`` path templates with a ``{value}``
# placeholder. All four current providers happen to share the ``account/`` and
# ``asset/`` address/asset paths and differ only on the transaction path, but the
# templates are kept per-entity so a future provider can diverge freely.
EXPLORERS = {
    "allo": {
        "name": "Allo",
        "base": "https://allo.info/",
        "address": "account/{value}",
        "asset": "asset/{value}",
        "transaction": "tx/{value}",
    },
    "lora": {
        "name": "Lora",
        "base": "https://lora.algokit.io/mainnet/",
        "address": "account/{value}",
        "asset": "asset/{value}",
        "transaction": "transaction/{value}",
    },
    "pera": {
        "name": "Pera Explorer",
        "base": "https://explorer.perawallet.app/",
        "address": "account/{value}",
        "asset": "asset/{value}",
        "transaction": "tx/{value}",
    },
    "algosurf": {
        "name": "Algo Surf",
        "base": "https://algo.surf/",
        "address": "account/{value}",
        "asset": "asset/{value}",
        "transaction": "transaction/{value}",
    },
}


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
        (key, conf["name"])
        for key, conf in EXPLORERS.items()
        if key != DEFAULT_EXPLORER
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
    """Return the full explorer URL for ``entity`` (``address``/``asset``/``transaction``).

    Falls back to the default explorer for an unknown key. An unknown ``entity``
    yields the bare base URL rather than raising, so a template typo degrades to
    a still-valid link.

    :param explorer: explorer key
    :type explorer: str
    :param entity: one of ``"address"``, ``"asset"``, ``"transaction"``
    :type entity: str
    :param value: address, asset id, or transaction id to embed
    :return: str
    """
    conf = EXPLORERS[normalized_explorer(explorer)]
    template = conf.get(entity)
    if template is None:
        return conf["base"]
    return conf["base"] + template.format(value=value)
