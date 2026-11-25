"""Template filters for the DAO voting pages."""

from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()

#: Classes for the rendered proposal; only utilities style.tw.css already has.
MARKDOWN_CLASSES = {
    "heading_open": "mt-6 mb-3",
    "paragraph_open": "mt-3",
    "bullet_list_open": "list-disc pl-6 mt-3",
    "ordered_list_open": "list-decimal pl-6 mt-3",
    "blockquote_open": "border-l-4 border-base-300 pl-4 italic mt-3",
    "table_open": "table mt-3",
    "fence": "block bg-base-200 rounded-box p-3 mt-3 overflow-x-auto text-sm",
    "code_block": "block bg-base-200 rounded-box p-3 mt-3 overflow-x-auto text-sm",
    "link_open": "link",
}

# html=False escapes raw HTML; markdown-it also refuses javascript:/data: links.
_MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")


def _add_classes(state):
    for token in state.tokens:
        for item in [token, *(token.children or [])]:
            css = MARKDOWN_CLASSES.get(item.type)
            if css:
                item.attrJoin("class", css)
            if item.type == "link_open":
                item.attrSet("rel", "nofollow noopener")


_MARKDOWN.core.ruler.push("dao_classes", _add_classes)


@register.filter
def markdown(text):
    """Return Markdown as HTML with raw HTML escaped.

    :param text: Markdown source
    :type text: str
    :return: str
    """
    return mark_safe(_MARKDOWN.render(text or ""))


@register.filter
def micro(value):
    """Return micro-units as whole units with thousands separators.

    :param value: amount in micro-units
    :type value: int
    :return: str
    """
    if value is None:
        return "-"
    text = f"{Decimal(value) / Decimal(1_000_000):,.6f}".rstrip("0").rstrip(".")
    return text or "0"


@register.filter
def grouped(value):
    """Return a whole number with thousands separators.

    :param value: whole number
    :type value: int
    :return: str
    """
    return "-" if value is None else f"{value:,}"


@register.filter
def short_address(address):
    """Return the first and last six characters of an address.

    :param address: public Algorand address
    :type address: str
    :return: str
    """
    return f"{address[:6]}…{address[-6:]}" if len(address) > 14 else address
