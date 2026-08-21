"""Deciding how much of a list to show before asking.

An address holding 76 assets shows the reader 76 rows, of which the first ten
account for almost all the money. The rest are dust, airdrops, and things that
went to zero -- worth keeping, not worth leading with.

One rule does this at every level: **show the rows that account for the first
``threshold`` of the section's weight, then offer the rest**. The count is
whatever that takes, so a wallet holding one asset shows one row and a wallet
holding two hundred near-identical ones shows nearly all of them. A fixed "top
ten" would be wrong at both ends.

**Weight is** ``abs(value)``\\ **, not value.** A borrow is negative by rule, so
a signed running total sails past the threshold and back again, hiding material
rows on the way. It also prints nonsense: an early version of this reported
"the last -68.8% of value". Ranking on magnitude asks the question that was
meant -- how much of what is going on here does this row account for -- and a
large debt is a large part of what is going on.
"""

from django.conf import settings


def magnitude(value):
    """Return ``abs(value)`` as a float, treating anything unusable as zero.

    The serialized payload is not uniform: an asset's value arrives as a float
    and an NFT row's as a decimal string. Coercing here rather than at each call
    site keeps that difference from becoming three subtly different rules.

    :param value: a row's value, in whatever form the payload carries it
    :return: float, never negative
    :rtype: float
    """
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return 0.0


def cutoff(weights, threshold=None, floor=None):
    """Return how many of ``weights`` to show, ranked by magnitude.

    The list is *not* reordered: the answer is a count, applied to the caller's
    own ordering. Sorting here would mean the reader's arrangement and the
    cutoff fighting over the same list.

    :param weights: each row's value, in the caller's display order
    :type weights: list
    :param threshold: share of total magnitude to reach, 0..1; defaults to
        ``settings.ADDRESS_SECTION_THRESHOLD``
    :type threshold: float | None
    :param floor: never hide a section down to fewer than this many rows;
        defaults to ``settings.ADDRESS_SECTION_FLOOR``
    :type floor: int | None
    :var total: summed magnitude of every row
    :type total: float
    :var running: magnitude accounted for so far
    :type running: float
    :return: how many rows to show, always at least ``min(floor, len(weights))``
    :rtype: int
    """
    if threshold is None:
        threshold = settings.ADDRESS_SECTION_THRESHOLD
    if floor is None:
        floor = settings.ADDRESS_SECTION_FLOOR

    count = len(weights)
    if count == 0:
        return 0
    # A threshold of 1 means "all of it", and floating-point summation will not
    # reliably reach 1.0 by the last row. Short-circuit rather than rely on it.
    if threshold >= 1:
        return count

    magnitudes = sorted((magnitude(w) for w in weights), reverse=True)
    total = sum(magnitudes)
    if total == 0:
        # Every row is worth nothing, so no row is more worth showing than any
        # other. The floor decides, not the ratio.
        return min(max(floor, 0), count)

    running = 0.0
    reached = count
    for index, weight in enumerate(magnitudes):
        running += weight
        if running / total >= threshold:
            reached = index + 1
            break

    return min(count, max(reached, floor))


def split(rows, weight_of, threshold=None, floor=None):
    """Split ``rows`` into the ones to show and the ones to offer.

    The cutoff is computed on magnitude but applied **in the caller's order**,
    so the rows shown are the first N as displayed rather than the N largest.
    Those differ whenever the list is not sorted by value, and showing a
    section's first rows is what the reader expects; showing an arbitrary
    subset with gaps is not.

    :param rows: the rows in display order
    :type rows: list
    :param weight_of: callable returning one row's value
    :type weight_of: callable
    :param threshold: see :func:`cutoff`
    :type threshold: float | None
    :param floor: see :func:`cutoff`
    :type floor: int | None
    :return: ``(shown, hidden)``
    :rtype: tuple
    """
    rows = list(rows)
    keep = cutoff([weight_of(row) for row in rows], threshold, floor)
    return rows[:keep], rows[keep:]
