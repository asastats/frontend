"""Testing module for website's jsonld data."""

import os

import pytest
from django.conf import settings


def snippet_for_item(folder, item):
    return os.path.join(
        settings.BASE_DIR, "../templates/jsonld/", folder, "{}.jsonld".format(item)
    )


@pytest.mark.parametrize(
    "item,title",
    [
        ("about", "About"),
        ("tokenomics", "Tokenomics"),
        ("faq", "FAQ page"),
        ("disclaimer", "Disclaimer"),
        ("asm-privacy", "{{ WEBSITE_NAME }} Mobile"),
        ("features", "features"),
        ("subscriptions", "Subscription plans"),
    ],
)
def test_accounts_pages_jsonld_content(item, title):
    path = snippet_for_item("", item)
    with open(path, "r") as f:
        fileread = f.read()
        for word in title.split(" "):
            assert word in fileread


@pytest.mark.parametrize(
    "item",
    [
        "about",
        "tokenomics",
        "faq",
        "disclaimer",
        "asm-privacy",
        "features",
        "subscriptions",
    ],
)
def test_pages_jsonld_content_id(item):
    path = snippet_for_item("", item)
    with open(path, "r") as f:
        fileread = f.read()
        page_id = '"@id":"{}/#{}"'.format("{{ WEBSITE_URL }}", item)
        assert page_id in fileread


def test_index_page_jsonld_file_exist():
    path = snippet_for_item(".", "index")
    assert os.path.exists(path) == 1
