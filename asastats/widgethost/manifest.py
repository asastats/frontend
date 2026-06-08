"""Loading, validation, and permission evaluation for widget manifests.

A widget describes itself in a ``widget.toml`` file. This module parses and
validates that description and evaluates the host-side ``required_permission``
gate (the forkable, per-user bar) against a resolved address count.
"""

import tomllib

VALID_ORIGINS = ("inhouse", "thirdparty")
VALID_CAPABILITIES = ("public", "engine-backed")
REQUIRED_FIELDS = (
    "id",
    "name",
    "version",
    "origin",
    "capability",
    "required_permission",
)


class ManifestError(Exception):
    """Raised when a widget manifest is missing or malformed."""


class Manifest:
    """Parsed and validated description of a single widget.

    :var Manifest.id: unique widget slug
    :type Manifest.id: str
    :var Manifest.name: human-readable widget name
    :type Manifest.name: str
    :var Manifest.version: widget version string
    :type Manifest.version: str
    :var Manifest.origin: provenance, one of inhouse or thirdparty
    :type Manifest.origin: str
    :var Manifest.capability: privilege level, one of public or engine-backed
    :type Manifest.capability: str
    :var Manifest.revenue_account: payout identifier for thirdparty widgets
    :type Manifest.revenue_account: str
    :var Manifest.required_permission: user-permission gate, integer or band list
    :type Manifest.required_permission: int or list
    :var Manifest.routes: route declarations served by the widget
    :type Manifest.routes: list
    :var Manifest.consumers: websocket consumer declarations
    :type Manifest.consumers: list
    :var Manifest.menu: optional menu entry declaration
    :type Manifest.menu: dict
    :var Manifest.engine_endpoints: declared privileged engine scopes
    :type Manifest.engine_endpoints: list
    :var Manifest.data: declared user-context keys the host must inject
    :type Manifest.data: list
    :var Manifest.hosts: declared external hosts the widget may call
    :type Manifest.hosts: list
    :var Manifest.assets: static and template directory declarations
    :type Manifest.assets: dict
    """

    def __init__(self, data):
        """Populate manifest attributes from the parsed mapping.

        :param data: parsed and validated widget.toml mapping
        :type data: dict
        """
        self.id = data["id"]
        self.name = data["name"]
        self.version = data["version"]
        self.origin = data["origin"]
        self.capability = data["capability"]
        self.revenue_account = data.get("revenue_account", "")
        self.required_permission = data["required_permission"]
        self.routes = data.get("routes", [])
        self.consumers = data.get("consumers", [])
        self.menu = data.get("menu")
        self.engine_endpoints = data.get("engine_endpoints", [])
        self.data = data.get("data", [])
        self.hosts = data.get("hosts", [])
        self.assets = data.get("assets", {})


def load_manifest(path):
    """Load, validate, and return the widget manifest stored at `path`.

    :param path: full path to a widget.toml file
    :type path: :class:`pathlib.Path`
    :var data: parsed widget.toml mapping
    :type data: dict
    :return: :class:`Manifest`
    """
    with open(path, "rb") as manifest_file:
        data = tomllib.load(manifest_file)
    validate_manifest(data)
    return Manifest(data)


def validate_manifest(data):
    """Raise :class:`ManifestError` when the manifest mapping is invalid.

    :param data: parsed widget.toml mapping
    :type data: dict
    :var field: currently checked required field name
    :type field: str
    """
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ManifestError(f"Manifest missing required field '{field}'.")
    if data["origin"] not in VALID_ORIGINS:
        raise ManifestError(f"Invalid origin '{data['origin']}'.")
    if data["capability"] not in VALID_CAPABILITIES:
        raise ManifestError(f"Invalid capability '{data['capability']}'.")
    if data["capability"] == "public" and data.get("engine_endpoints"):
        raise ManifestError("A public widget must not declare engine_endpoints.")
    if data["capability"] == "engine-backed" and not data.get("engine_endpoints"):
        raise ManifestError("An engine-backed widget must declare engine_endpoints.")
    _validate_required_permission(data["required_permission"])


def _validate_required_permission(required_permission):
    """Raise :class:`ManifestError` when required_permission is malformed.

    :param required_permission: integer or ordered band list
    :type required_permission: int or list
    :var band: currently checked permission band mapping
    :type band: dict
    """
    if isinstance(required_permission, bool):
        raise ManifestError("required_permission must be an int or a band list.")
    if isinstance(required_permission, int):
        return
    if not isinstance(required_permission, list) or not required_permission:
        raise ManifestError("required_permission must be an int or a band list.")
    for band in required_permission:
        if "max_addresses" not in band or "permission" not in band:
            raise ManifestError("Each band needs 'max_addresses' and 'permission'.")


def required_permission_for_size(required_permission, size):
    """Return the permission integer required for `size` addresses, or None.

    None means `size` exceeds the largest band and access must be denied.

    :param required_permission: integer or ordered band list
    :type required_permission: int or list
    :param size: number of resolved Algorand addresses
    :type size: int
    :var band: currently evaluated permission band mapping
    :type band: dict
    :return: int
    """
    if isinstance(required_permission, int):
        return required_permission
    for band in required_permission:
        if size <= band["max_addresses"]:
            return band["permission"]
    return None


def can_access(profile_permission, required_permission, size):
    """Return whether a user with `profile_permission` may use the widget.

    :param profile_permission: the user's permission integer
    :type profile_permission: int
    :param required_permission: integer or ordered band list from the manifest
    :type required_permission: int or list
    :param size: number of resolved Algorand addresses
    :type size: int
    :var required: permission integer needed for the given size, or None
    :type required: int
    :return: Boolean
    """
    required = required_permission_for_size(required_permission, size)
    if required is None:
        return False
    return profile_permission >= required
