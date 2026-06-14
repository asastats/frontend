"""Template tags for embedding the wallet connector on any page.

Exposing the supported-wallet list as a tag lets the sign-in partial be dropped
into the allauth login template (or anywhere) without a custom view or context
processor: ``{% supported_wallets as wallets %}`` then iterate.
"""

from django import template

from utils.constants.core import ALGORAND_WALLETS

register = template.Library()


@register.simple_tag
def supported_wallets():
    """Return the supported-wallet descriptors for card rendering.

    :return: list of ``{"id", "name"}`` wallet descriptors
    :rtype: list
    """
    return ALGORAND_WALLETS
