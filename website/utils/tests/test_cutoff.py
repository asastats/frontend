"""Tests for :mod:`utils.cutoff`."""

import pytest
from django.conf import settings

from utils.cutoff import cutoff, split


class TestUtilsCutoffCount:
    """Testing class for :func:`cutoff`."""

    def test_utils_cutoff_empty_list_shows_nothing(self):
        assert cutoff([]) == 0

    def test_utils_cutoff_threshold_of_one_shows_everything(self):
        """Short-circuited rather than trusted to sum to 1.0.

        Floating-point summation does not reliably reach the total by the last
        row, so a 1.0 threshold computed the long way can hide the final entry.
        """
        assert cutoff([1.0] * 7, threshold=1, floor=0) == 7

    def test_utils_cutoff_leading_row_carries_the_section(self):
        assert cutoff([99.0, 0.5, 0.3, 0.2], threshold=0.9, floor=0) == 1

    def test_utils_cutoff_takes_as_many_rows_as_it_needs(self):
        assert cutoff([25.0, 25.0, 25.0, 25.0], threshold=0.9, floor=0) == 4

    def test_utils_cutoff_even_split_at_half(self):
        assert cutoff([10.0, 10.0, 10.0, 10.0], threshold=0.5, floor=0) == 2

    def test_utils_cutoff_floor_wins_when_it_is_higher(self):
        assert cutoff([99.0, 0.5, 0.3, 0.2], threshold=0.9, floor=3) == 3

    def test_utils_cutoff_floor_cannot_exceed_the_list(self):
        assert cutoff([99.0, 1.0], threshold=0.9, floor=50) == 2

    def test_utils_cutoff_ranks_on_magnitude_not_order(self):
        """The list is not sorted, so the answer must not depend on its order."""
        ascending = cutoff([0.2, 0.3, 0.5, 99.0], threshold=0.9, floor=0)
        descending = cutoff([99.0, 0.5, 0.3, 0.2], threshold=0.9, floor=0)

        assert ascending == descending == 1

    def test_utils_cutoff_a_borrow_counts_towards_the_share(self):
        """A debt is a large part of what is going on, so it ranks large.

        Signed, this list totals 1.0 and the first row alone would look like
        9900% of it -- which is how an early version came to report "the last
        -68.8% of value".
        """
        assert cutoff([99.0, -98.0, 0.5, 0.5], threshold=0.9, floor=0) == 2

    def test_utils_cutoff_all_negative_behaves_like_all_positive(self):
        assert cutoff([-99.0, -0.5, -0.3, -0.2], threshold=0.9, floor=0) == 1

    def test_utils_cutoff_worthless_section_falls_to_the_floor(self):
        """No row is more worth showing than any other, so the ratio is mute."""
        assert cutoff([0, 0, 0, 0, 0], threshold=0.9, floor=3) == 3

    def test_utils_cutoff_worthless_section_with_no_floor_shows_nothing(self):
        assert cutoff([0, 0, 0], threshold=0.9, floor=0) == 0

    def test_utils_cutoff_tolerates_none_values(self):
        """A missing value is worth nothing, not a crash."""
        assert cutoff([10.0, None, None], threshold=0.9, floor=0) == 1

    def test_utils_cutoff_reads_decimal_strings(self):
        """The payload is not uniform.

        An asset's value arrives as a float and an NFT row's as a decimal
        string, and the same rule has to serve both.
        """
        assert cutoff(["99.000000", "0.500000", "0.500000"], threshold=0.9, floor=0) == 1

    def test_utils_cutoff_mixed_types_rank_together(self):
        assert cutoff([99.0, "0.500000", None], threshold=0.9, floor=0) == 1

    def test_utils_cutoff_ignores_unparseable_values(self):
        assert cutoff([10.0, "not a number"], threshold=0.9, floor=0) == 1

    @pytest.mark.parametrize("threshold", [0.5, 0.9, 0.99, 0.995])
    def test_utils_cutoff_never_exceeds_the_list(self, threshold):
        assert cutoff([1.0] * 5, threshold=threshold, floor=0) <= 5

    @pytest.mark.parametrize("threshold", [0.5, 0.9, 0.99, 0.995])
    def test_utils_cutoff_shown_rows_do_reach_the_threshold(self, threshold):
        """The point of the rule, asserted rather than assumed."""
        weights = [50.0, 20.0, 15.0, 8.0, 4.0, 2.0, 1.0]
        keep = cutoff(weights, threshold=threshold, floor=0)
        ranked = sorted(weights, reverse=True)

        assert sum(ranked[:keep]) / sum(ranked) >= threshold

    def test_utils_cutoff_defaults_come_from_settings(self):
        """So a deployment can retune this without a code change."""
        weights = [1.0] * 40

        assert cutoff(weights) == cutoff(
            weights,
            threshold=settings.ADDRESS_SECTION_THRESHOLD,
            floor=settings.ADDRESS_SECTION_FLOOR,
        )


class TestUtilsCutoffSplit:
    """Testing class for :func:`split`."""

    def test_utils_cutoff_split_returns_both_halves(self):
        shown, hidden = split([3, 2, 1], lambda row: row, threshold=0.5, floor=0)

        assert shown + hidden == [3, 2, 1]

    def test_utils_cutoff_split_keeps_the_callers_order(self):
        """Applied in display order, not value order.

        Showing the N largest rows would leave gaps in the list -- rows 1, 4
        and 9 visible and the rest folded -- which reads as a rendering fault.
        The reader expects the first N.
        """
        rows = [1, 2, 3, 99]
        shown, hidden = split(rows, lambda row: row, threshold=0.9, floor=2)

        assert shown == [1, 2]
        assert hidden == [3, 99]

    def test_utils_cutoff_split_of_an_empty_list(self):
        assert split([], lambda row: row) == ([], [])

    def test_utils_cutoff_split_reads_the_weight_through_the_callable(self):
        rows = [{"v": 99.0}, {"v": 0.5}, {"v": 0.5}]
        shown, hidden = split(rows, lambda row: row["v"], threshold=0.9, floor=0)

        assert shown == [{"v": 99.0}]
        assert len(hidden) == 2

    def test_utils_cutoff_split_does_not_consume_an_iterator(self):
        """Callers pass querysets and generators; both halves must be real."""
        shown, hidden = split(
            iter([3, 2, 1]), lambda row: row, threshold=0.5, floor=0
        )

        assert shown == [3]
        assert hidden == [2, 1]
