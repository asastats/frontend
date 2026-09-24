"""Module containing the address-page layout registry.

:data:`ADDRESS_LAYOUTS` maps a layout key to its display name, one-line
summary, template, compact flag and minimum subscription tier. Adding an entry
there makes the layout selectable on the settings page with no change here.

Entitlement varies per entry, unlike every other preference on that page, so
every function below that returns a layout takes the reader's permission value
and answers for that reader.

**Entitlement is re-checked on read**, unlike a saved explorer: the layout
*is* the subscription benefit, so a lapsed reader falls back to the default
while their choice is remembered for when they return.
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
    page names them and the tier each one needs.

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


def layout_template(layout):
    """Return the template ``layout`` renders.

    Unknown keys fall back to the default's template, so a key left behind by a
    removed layout renders the default page rather than raising
    ``TemplateDoesNotExist`` at the top of a view.

    Several layouts may name the same template, so this is not an identity.
    Use the layout key itself wherever one is needed, notably for the cache.

    :param layout: layout key
    :type layout: str
    :return: str
    """
    conf = ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])
    return conf["template"]


def layout_compact(layout):
    """Return True if ``layout`` renders its template's dense form.

    Kept apart from :func:`layout_template` rather than folded into a single
    "variant" string, because the two are asked in different places: the view
    picks the file, the markup adds one class.

    :param layout: layout key
    :type layout: str
    :return: bool
    """
    conf = ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])
    return conf["compact"]


def layout_for_user(user):
    """Return the layout key a page should render for ``user``.

    The one entry point a view needs. Anonymous readers and the rare user row
    with no profile get the default: there is no preference to read and no tier
    to check.

    Takes the user rather than the profile, and duck-types both, so a caller
    need not know which case it is in and this module keeps its independence
    from ``django.contrib.auth``.

    ``None`` means the same as anonymous. A request that never passed through
    ``AuthenticationMiddleware`` has no ``user`` at all, and raising there would
    turn a middleware ordering change into a 500 on the busiest page on the
    site.

    :param user: the request's user (may be anonymous)
    :type user: :class:`User` or :class:`AnonymousUser`
    :var profile: the user's profile, or None
    :type profile: :class:`Profile` or None
    :return: a key guaranteed to exist in :data:`ADDRESS_LAYOUTS`
    :rtype: str
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return DEFAULT_ADDRESS_LAYOUT
    profile = getattr(user, "profile", None)
    if profile is None:
        return DEFAULT_ADDRESS_LAYOUT
    return profile.preferred_layout_or_default()


def layout_tier(layout):
    """Return the minimum tier name for ``layout``, or None if ungated.

    Used to tell a reader below the line which tier unlocks what they are
    looking at.

    :param layout: layout key
    :type layout: str
    :return: str or None
    """
    return ADDRESS_LAYOUTS.get(layout, ADDRESS_LAYOUTS[DEFAULT_ADDRESS_LAYOUT])["tier"]
