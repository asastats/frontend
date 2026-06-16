"""Testing module for core app middleware module."""

import pytest
from django_minify_html.middleware import MinifyHtmlMiddleware

from core.middleware import CustomMinifyHtmlMiddleware


class TestCoreMiddleware:
    """Testing class for :py:mod:`website.core.middleware` module."""

    # # CustomMinifyHtmlMiddleware
    def test_core_middleware_customminifyhtmlmiddleware_is_subclass(self):
        assert issubclass(CustomMinifyHtmlMiddleware, MinifyHtmlMiddleware)

    @pytest.mark.parametrize(
        "arg",
        [
            "minify_css",
            "minify_js",
            "minify_doctype",
            "allow_removing_spaces_between_attributes",
            "allow_noncompliant_unquoted_attribute_values",
        ],
    )
    def test_core_middleware_customminifyhtmlmiddleware_sets_arg_to_false(self, arg):
        assert CustomMinifyHtmlMiddleware.minify_args.get(arg) is False

    @pytest.mark.parametrize(
        "arg",
        ["keep_closing_tags"],
    )
    def test_core_middleware_customminifyhtmlmiddleware_sets_arg_to_true(self, arg):
        assert CustomMinifyHtmlMiddleware.minify_args.get(arg) is True
