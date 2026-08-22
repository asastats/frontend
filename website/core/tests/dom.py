"""A very small queryable DOM, built on the standard library.

There is no HTML parsing library in this project's test requirements, and the
existing template tests either match raw substrings or hand-roll an
``html.parser`` subclass for one assertion at a time. Substring matching is the
wrong tool for a structural contract -- it passes when an attribute drifts onto
the wrong element and fails when the whitespace changes -- so this gives the
tests a real tree to ask questions of without adding a dependency.

Deliberately not a CSS engine. It supports exactly the selector forms
``core.tests.test_selector_contract`` needs, and raises on anything else rather
than silently matching nothing::

    tag                     div
    .class                  .fitem
    #id                     #id-cons
    tag.class               span.val
    .a.b                    .token.item-header
    [attr]                  [data-program-panel]
    [attr="value"]          input[type="checkbox"]
    tag.class[attr]         img.nft[data-src]
    <step> <step>           descendant
    <sel>, <sel>            either

A selector that quietly matches nothing is how a contract test ends up
green against a page that no longer has the element.
"""

import re
from html.parser import HTMLParser

#: Elements that never have a closing tag, so they never open a scope.
VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)

#: Elements whose content is text, not markup, and must not be descended into.
RAW_TEXT_TAGS = frozenset({"script", "style"})


class Element:
    """One node in the parsed tree.

    :var tag: lowercased element name
    :type tag: str
    :var attrs: attribute map; a valueless attribute maps to the empty string
    :type attrs: dict
    :var parent: the containing element, or ``None`` for the root
    :type parent: Element | None
    """

    __slots__ = ("tag", "attrs", "parent", "children", "_text")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.parent = parent
        self.children = []
        self._text = []

    # -- attribute access -------------------------------------------------

    def get(self, name, default=None):
        """Attribute value, or `default`.

        :param name: attribute name
        :type name: str
        :return: str | None
        """
        return self.attrs.get(name, default)

    def has_attr(self, name):
        """Whether the attribute is present, including when it has no value.

        :param name: attribute name
        :type name: str
        :return: bool
        """
        return name in self.attrs

    def __getitem__(self, name):
        return self.attrs[name]

    @property
    def classes(self):
        """The element's class tokens.

        :return: set
        """
        return set((self.attrs.get("class") or "").split())

    # -- traversal --------------------------------------------------------

    def descendants(self):
        """Every element below this one, depth first.

        :return: iterator of Element
        """
        for child in self.children:
            yield child
            yield from child.descendants()

    def ancestors(self):
        """Every element above this one, nearest first.

        :return: iterator of Element
        """
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def find_parent(self, class_=None, attr=None, tag=None):
        """Nearest ancestor matching the given constraint, or ``None``.

        :param class_: a single class token the ancestor must carry
        :type class_: str | None
        :param attr: an attribute name the ancestor must have
        :type attr: str | None
        :param tag: an element name the ancestor must be
        :type tag: str | None
        :return: Element | None
        """
        for node in self.ancestors():
            if class_ is not None and class_ not in node.classes:
                continue
            if attr is not None and not node.has_attr(attr):
                continue
            if tag is not None and node.tag != tag:
                continue
            return node
        return None

    # -- content ----------------------------------------------------------

    def text(self, strip=True):
        """All text in this element and its descendants, in document order.

        Order matters and used not to be kept: this put the element's own text
        nodes first and its children's after, so ``<a> <span>Ada</span>
        <span>ada@x</span></a>`` read back as ``Adaada@x`` -- the separating
        space was real, sat between the two spans, and was reported before both
        of them. What a screen reader announces is exactly this string, so a
        test asking whether two facts run together got the wrong answer.

        Each text node remembers how many children preceded it, which is what
        makes the interleaving possible.

        :param strip: collapse surrounding whitespace
        :type strip: bool
        :return: str
        """
        parts = []
        cursor = 0
        for position, chunk in self._text:
            while cursor < position:
                parts.append(self.children[cursor].text(strip=False))
                cursor += 1
            parts.append(chunk)
        while cursor < len(self.children):
            parts.append(self.children[cursor].text(strip=False))
            cursor += 1
        joined = "".join(parts)
        return joined.strip() if strip else joined

    def has_element_children(self):
        """Whether this element contains markup rather than only text.

        The currency switch assigns ``innerHTML`` over several spans, so a
        child element there is destroyed on the first switch.

        :return: bool
        """
        return bool(self.children)

    # -- querying ---------------------------------------------------------

    def select(self, selector):
        """Every descendant matching `selector`, in document order.

        :param selector: see the module docstring for the supported grammar
        :type selector: str
        :return: list of Element
        """
        matched, seen = [], set()
        for alternative in selector.split(","):
            for node in self._select_one_alternative(alternative.strip()):
                if id(node) not in seen:
                    seen.add(id(node))
                    matched.append(node)
        order = {id(n): i for i, n in enumerate(self.descendants())}
        return sorted(matched, key=lambda n: order[id(n)])

    def _select_one_alternative(self, selector):
        scopes = [self]
        for step in selector.split():
            matcher = _compile(step)
            found, seen = [], set()
            for scope in scopes:
                for node in scope.descendants():
                    if matcher(node) and id(node) not in seen:
                        seen.add(id(node))
                        found.append(node)
            scopes = found
        return scopes

    def select_one(self, selector):
        """First descendant matching `selector`, or ``None``.

        :param selector: see the module docstring
        :type selector: str
        :return: Element | None
        """
        found = self.select(selector)
        return found[0] if found else None

    def by_id(self, value):
        """Every descendant carrying this id.

        Returns a list rather than one element on purpose: duplicated ids are
        exactly what several of these tests are looking for.

        :param value: the id to match
        :type value: str
        :return: list of Element
        """
        return [n for n in self.descendants() if n.get("id") == value]

    def __repr__(self):
        bits = "".join(f' {k}="{v}"' for k, v in list(self.attrs.items())[:3])
        return f"<{self.tag}{bits}>"


#: One token inside a compound selector.
_TOKEN = r"[.#][\w-]+|\[[\w-]+(?:=(?:\"[^\"]*\"|'[^']*'|[\w-]+))?\]"

#: One simple selector: optional tag, any number of .classes, one #id,
#: any number of [attributes].
_STEP = re.compile(r"^(?P<tag>[a-zA-Z][\w-]*)?(?P<rest>(?:" + _TOKEN + r")*)$")


def _compile(step):
    """Turn one simple selector into a predicate.

    :param step: a single compound selector, no combinators
    :type step: str
    :return: callable
    :raises ValueError: on anything the grammar does not cover
    """
    match = _STEP.match(step)
    if not match:
        raise ValueError(
            f"unsupported selector {step!r}; see core.tests.dom for the grammar"
        )
    tag = match.group("tag")
    classes, ids, attrs = [], [], []
    for token in re.findall(_TOKEN, match.group("rest")):
        if token.startswith("."):
            classes.append(token[1:])
        elif token.startswith("#"):
            ids.append(token[1:])
        else:
            name, _, value = token[1:-1].partition("=")
            attrs.append((name, value.strip("\"'") if value else None))

    def matches(node):
        if tag and node.tag != tag:
            return False
        if ids and node.get("id") not in ids:
            return False
        if not set(classes) <= node.classes:
            return False
        for name, value in attrs:
            if not node.has_attr(name):
                return False
            if value is not None and node.get(name) != value:
                return False
        return True

    return matches


class _Builder(HTMLParser):
    """Assemble an :class:`Element` tree, tolerating unclosed tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("[document]")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        # Walk back to the matching open tag rather than popping blindly: a
        # stray `</div>` in a template would otherwise re-parent the entire
        # rest of the page and make every structural assertion meaningless.
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                del self.stack[depth:]
                return

    def handle_data(self, data):
        # Paired with the number of children already seen, so `text()` can put
        # it back where it was rather than in front of all of them.
        node = self.stack[-1]
        node._text.append((len(node.children), data))


def parse(html):
    """Parse a document and return its root element.

    :param html: rendered markup
    :type html: str
    :return: Element
    """
    builder = _Builder()
    builder.feed(html)
    builder.close()
    return builder.root
