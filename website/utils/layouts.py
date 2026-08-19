"""Module containing the address-page layout registry.

A single table (:data:`ADDRESS_LAYOUTS`) maps a layout key to its display name,
one-line summary, position-component modifier, and minimum subscription tier.
Adding an entry there makes the layout selectable on the user settings page with
no change here, the way an explorer becomes selectable by joining
:data:`EXPLORERS` and a swap router by being discovered.

The one difference from the explorer registry is that entitlement varies *per
entry*. Every other preference on that page is a single gate -- you may choose
an explorer, or you may not -- while the layouts are handed out in stages, so
every function below that returns a layout takes the reader's permission value
and answers for that reader.

**Entitlement is re-checked on read**, unlike
:meth:`Profile.preferred_explorer_or_default`. A saved explorer keeps applying
after a subscription lapses because every explorer is worth the same; a saved
layout does not, because the layout *is* the subscription benefit. A lapsed
reader falls back to the default rather than keeping what they no longer pay
for, and their choice is remembered for when they return.
"""

from utils.constants.core import ADDRESS_LAYOUTS, DEFAULT_ADDRESS_LAYOUT
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


def _entitled(layout, permission):
    """Return True if ``permission`` reaches the tier ``layout`` requires.

    :param layout: layout key, assumed to exist in :data:`ADDRESS_LAYOUTS`
    :type layout: str
    :param permission: the reader's permission value
    :type permission: int
    :return: bool
    """
    tier = ADDRESS_LAYOUTS[layout]["tier"]
    return tier is None or permission >= SUBSCRIPTION_TIER_PERMISSIONS[tier]


def can_access_layout(layout, permission):
    """Return True if ``permission`` may select ``layout``.

    An unknown key is not accessible: it names nothing to render, so treating it
    as available would put a value in the database that no page can honour.

    :param layout: candidate layout key (may be empty/unknown/None)
    :type layout: str
    :param permission: the reader's permission value
    :type permission: int
    :return: bool
    """
    return layout in ADDRESS_LAYOUTS and _entitled(layout, permission)


def normalized_layout(layout, permission):
    """Return ``layout`` if it is known and permitted, otherwise the default.

    Both failure modes collapse to the same answer on purpose. A key that no
    longer exists and a key the reader may no longer use are the same problem
    for a template -- there is nothing to render -- and the default is always
    entitled, so this cannot fail.

    :param layout: candidate layout key (may be empty/unknown/None)
    :type layout: str
    :param permission: the reader's permission value
    :type permission: int
    :return: a key guaranteed to exist in :data:`ADDRESS_LAYOUTS`
    :rtype: str
    """
    if can_access_layout(layout, permission):
        return layout
    return DEFAULT_ADDRESS_LAYOUT


def layout_choices(permission):
    """Return ``(key, name)`` pairs the reader may choose, default first.

    Only entitled layouts are returned, which is what makes a forged POST fail
    validation rather than needing a second check in the view: the form's
    choices *are* the entitlement.

    :param permission: the reader's permission value
    :type permission: int
    :var default: the default layout's ``(key, name)`` pair
    :type default: tuple
    :var others: remaining entitled layouts, in registry order
    :type others: list
    :return: list of two-tuples
    :rtype: list
    """
    default = (DEFAULT_ADDRESS_LAYOUT, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT]["name"])
    others = [
        (key, conf["name"])
        for key, conf in ADDRESS_LAYOUTS.items()
        if key != DEFAULT_ADDRESS_LAYOUT and _entitled(key, permission)
    ]
    return [default, *others]


def locked_layouts(permission):
    """Return the layouts ``permission`` does *not* reach, with their tiers.

    The counterpart to :func:`layout_choices`. A reader offered two of four
    options is otherwise left to guess whether the rest exist, so the settings
    page names them and the tier each one needs -- the same courtesy the
    explorer section pays by naming Intro.

    :param permission: the reader's permission value
    :type permission: int
    :return: list of dicts with ``name``, ``summary`` and ``tier`` keys
    :rtype: list
    """
    return [
        {"name": conf["name"], "summary": conf["summary"], "tier": conf["tier"]}
        for key, conf in ADDRESS_LAYOUTS.items()
        if not _entitled(key, permission)
    ]


def layout_name(layout):
    """Return the display name for ``layout`` (default's name if unknown).

    Takes no permission: this answers "what is this layout called", which is the
    same answer for everybody, and is used to label a layout the reader cannot
    yet have.

    :param layout: layout key
    :type layout: str
    :return: str
    """
    return ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])["name"]


def layout_position(layout):
    """Return the position-component modifier ``layout`` renders with.

    One of ``"rows"`` or ``"cards"``, completing ``.position--<modifier>`` in
    ``templates/snippets/asas/position.html``. Unknown keys fall back to the
    default's, so a stale value renders the default page rather than a component
    with no grid areas and overlapping children.

    :param layout: layout key
    :type layout: str
    :return: str
    """
    conf = ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])
    return conf["position"]


def layout_for_user(user):
    """Return the ``(key, position)`` pair a page should render for ``user``.

    The one entry point a view needs. Anonymous readers, and the rare user row
    with no profile attached, get the default -- there is no preference to read
    and no tier to check, so there is nothing to decide.

    Takes the user rather than the profile so a caller does not have to know
    which of those two cases it is in, and duck-types both so this module keeps
    its independence from ``django.contrib.auth``.

    :param user: the request's user (may be anonymous)
    :type user: :class:`User` or :class:`AnonymousUser`
    :var profile: the user's profile, or None
    :type profile: :class:`Profile` or None
    :return: ``(layout key, position modifier)``
    :rtype: tuple
    """
    profile = getattr(user, "profile", None) if user.is_authenticated else None
    if profile is None:
        return DEFAULT_ADDRESS_LAYOUT, layout_position(DEFAULT_ADDRESS_LAYOUT)
    layout = profile.preferred_layout_or_default()
    return layout, layout_position(layout)


def layout_tier(layout):
    """Return the minimum tier name for ``layout``, or None if ungated.

    Used to tell a reader below the line *which* tier unlocks what they are
    looking at, the way the explorer section names Intro.

    :param layout: layout key
    :type layout: str
    :return: str or None
    """
    return ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])["tier"]
