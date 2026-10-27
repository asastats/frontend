"""Template tags for embedding the wallet connector on any page.

Exposing the supported-wallet list as a tag lets the sign-in partial be dropped
into the allauth login template (or anywhere) without a custom view or context
processor: ``{% supported_wallets as wallets %}`` then iterate.
"""

from django import template

from core.appclient import supported_wallets as wallets_for

register = template.Library()


@register.simple_tag(takes_context=True)
def supported_wallets(context):
    """Return the wallet descriptors this request can use, for card rendering.

    :param context: template context carrying ``request``
    :type context: :class:`django.template.Context`
    :return: list of ``{"id", "name"}`` wallet descriptors
    :rtype: list
    """
    return wallets_for(context["request"])
