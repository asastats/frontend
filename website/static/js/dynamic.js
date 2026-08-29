/**
 * @file Charts for the dynamic address designs, drawn as inline SVG.
 *
 * Design 1 keeps Chart.js. Designs 2 and 3 draw their own, for four reasons:
 *
 *   * **Theming.** The site ships 57 themes. An SVG `fill` can be a
 *     `var(--color-...)` and repaints itself when the theme changes; a canvas
 *     must be handed literal hex at draw time, which is why design 1's palette
 *     is hardcoded and why a theme switch cannot recolour its charts without
 *     re-reading computed styles and redrawing.
 *   * **Interaction.** A slice here is a real element with a `<title>`, so it
 *     can be hovered, focused and described. Canvas slices are pixels needing
 *     hit-testing and a separate event path -- which is exactly why
 *     `chartClick` is the function the selector contract lists as known-broken.
 *     Under SVG that bug class stops existing rather than being ported.
 *   * **Size.** Around 200 KB of Chart.js for five slices.
 *   * **Accessibility.** A canvas is opaque to a screen reader.
 *
 * The payload is unchanged: the same six `json_script` blocks design 1 emits,
 * in the same Chart.js-shaped `{labels, datasets: [{data, backgroundColor}]}`.
 * Only the renderer differs, so the JSON API and the website keep one source
 * of truth.
 *
 * Nothing is drawn until the reader opens the charts panel. Six donuts of SVG
 * is a great deal of markup to hand someone who never looks at it.
 */
(function () {
  "use strict";

  /** Marks the panel bound, so a second execution cannot double-bind. */
  var BOUND_ATTR = "data-dynamic-bound";

  /** The same guard for the delegated breakdown handler, on the root element. */
  var BREAKDOWN_ATTR = "data-dynamic-breakdowns-bound";

  /** Radii of the ring, in the 120x120 user space the viewBox sets up. */
  var INNER = 34;
  var OUTER = 56;
  var CENTRE = 60;

  var SVG_NS = "http://www.w3.org/2000/svg";

  /** Labels the reader has crossed out, per chart element. */
  var CROSSED_PROP = "_asastatsCrossed";

  /**
   * The five payload blocks, in the order they are drawn.
   *
   * `nftfloorchart` is deliberately last: it is the least-asked question on the
   * page, and a reader scanning left to right should meet the allocation and
   * the top assets first.
   *
   * `total` names what the payload's percentages are a percentage *of*, read
   * off the header's own data attributes in ALGO. Four of the five blocks carry
   * shares rather than amounts -- `"46.30882653"` means 46.3% of the assets, not
   * 46.3 ALGO -- and the legend was printing those bare, so a reader saw a
   * column of figures in the same shape as every other figure on the page and
   * none of them were money. `distchart` is the exception and says so.
   */
  var CHARTS = [
    { id: "ratiochart", title: "Allocation", total: "everything" },
    { id: "distchart", title: "Top assets", absolute: true },
    { id: "asachart", title: "Assets by value", total: "assets" },
    { id: "nftchart", title: "NFT collections", total: "nft" },
    { id: "nftfloorchart", title: "NFT floor value", total: "nftfloor" },
  ];

  /**
   * Read and parse one `json_script` block.
   *
   * @param {string} id - the element id.
   * @returns {Object|null} the parsed payload, or null if absent or malformed.
   */
  function payload(id) {
    var node = document.getElementById(id);
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (error) {
      // A malformed block costs its own chart, not the whole panel.
      return null;
    }
  }

  /**
   * Return the colour for one slice of a payload.
   *
   * Chart.js accepts `backgroundColor` as either an array -- one colour per
   * label -- or a single string for the whole dataset, and the payloads use
   * both. Indexing a string gives *characters*: `"#005a34"[1]` is `"0"`, which
   * is not a colour, and the "Top assets" donut was drawn entirely in invalid
   * fills because of it.
   *
   * A stacked payload has one colour per *category*, so no colour of its own
   * for a per-label total. `palette` is the way out: the assets chart names the
   * same labels and carries a colour for each, so a lookup by name gives the
   * same asset the same colour in both charts. By name and not by index -- the
   * two payloads happen to agree on order today, and a lookup that depends on
   * that is a lookup that breaks silently.
   *
   * @param {Array} sets - the payload's datasets.
   * @param {number} index - the label's position.
   * @param {string} label - the label itself.
   * @param {Object} palette - label to colour, for stacked payloads.
   * @returns {string} a CSS colour.
   */
  function colorFor(sets, index, label, palette) {
    if (sets.length === 1) {
      var only = (sets[0] || {}).backgroundColor;
      if (Array.isArray(only)) return only[index] || "currentColor";
      if (typeof only === "string" && only) return only;
    }
    return (palette && palette[label]) || "currentColor";
  }

  /**
   * Flatten a Chart.js-shaped payload into slices.
   *
   * **Stacked payloads are summed, not truncated.** `distchart` carries one
   * dataset per allocation category -- Balance, Staked, Liquidity, DeFi -- and
   * this used to read `datasets[0]` alone, so "Top assets" was really "top
   * *wallet balances*": an asset held entirely in a liquidity pool was drawn as
   * nothing, and the donut did not add up to the section it sat under.
   *
   * @param {Object} data - `{labels, datasets: [{data, backgroundColor}]}`.
   * @param {Object} [palette] - label to colour, for stacked payloads.
   * @returns {Array} `[{label, value, color}]`, empty if there is nothing.
   */
  function slices(data, palette) {
    if (!data || !data.labels || !data.datasets || !data.datasets.length) {
      return [];
    }
    var sets = data.datasets;
    return data.labels
      .map(function (label, index) {
        var value = 0;
        sets.forEach(function (set) {
          value += parseFloat(((set || {}).data || [])[index]) || 0;
        });
        return {
          label: String(label),
          value: value,
          color: colorFor(sets, index, String(label), palette),
        };
      })
      .filter(function (slice) {
        // Magnitude: a borrowed position is negative and cannot be drawn a
        // negative arc, but a zero slice is genuinely nothing to draw.
        return Math.abs(slice.value) > 0;
      });
  }

  /**
   * Return a label-to-colour map from a payload with per-label colours.
   *
   * @param {Object} data - a payload, or null.
   * @returns {Object} label to colour; empty when the payload has no array.
   */
  function palette(data) {
    var found = {};
    if (!data || !data.labels || !data.datasets || !data.datasets.length) {
      return found;
    }
    var colors = (data.datasets[0] || {}).backgroundColor;
    if (!Array.isArray(colors)) return found;
    data.labels.forEach(function (label, index) {
      if (colors[index]) found[String(label)] = colors[index];
    });
    return found;
  }

  /* ---------------------------------------------------------------- money */

  /**
   * Read one figure off the page header, in ALGO.
   *
   * The same element and the same attributes `toolbar.js` reads, so the charts
   * and the rows cannot come to different conclusions about what the address is
   * worth.
   *
   * @param {string} name - the attribute, without its `data-` prefix.
   * @returns {number} the figure, or 0.
   */
  function headline(name) {
    var head = document.querySelector(".dynamic-page .pricetip");
    var value = head ? parseFloat(head.getAttribute("data-" + name)) : NaN;
    return isFinite(value) ? value : 0;
  }

  /**
   * Return what a chart's percentages are a percentage of, in ALGO.
   *
   * @param {string} of - the `total` key from `CHARTS`.
   * @returns {number} the whole, in ALGO.
   */
  function whole(of) {
    if (of === "everything") return headline("totalwnft");
    if (of === "assets") return headline("totalwnft") - headline("totalnft");
    if (of === "nft") return headline("totalnft");
    if (of === "nftfloor") return headline("totalnftfloor");
    return 0;
  }

  /**
   * Return the multiplier that turns a payload value into ALGO.
   *
   * @param {Object} spec - one entry from `CHARTS`.
   * @returns {number} 1 for an amount, `whole / 100` for a share.
   */
  function scaleFor(spec) {
    return spec.absolute ? 1 : whole(spec.total) / 100;
  }

  /**
   * @returns {string} the currency the page is showing, "ALGO" or "USD".
   */
  function currency() {
    try {
      return window.localStorage.getItem("cur") === "USD" ? "USD" : "ALGO";
    } catch (error) {
      // A browser refusing storage is not a reason to draw no charts.
      return "ALGO";
    }
  }

  /**
   * Format one ALGO figure in the page's currency, with no unit.
   *
   * The rule is `toolbar.js`'s, deliberately - see `fmt` there for why it is
   * exactly two decimals and why the previous widening rule was removed. The
   * two must agree: a chart legend and the asset row it describes are the same
   * figure, and a reader who sees them disagree has no way to tell which one
   * is rounded.
   *
   * @param {number} algo - the figure, in ALGO.
   * @returns {string} the formatted number.
   */
  function money(algo) {
    var value = currency() === "USD" ? algo * headline("pricealgo") : algo;
    if (!isFinite(value)) value = 0;
    return value.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  /**
   * Build one donut slice's path data, from `from` to `to` in turns.
   *
   * @param {number} from - start, in turns from twelve o'clock.
   * @param {number} to - end, in turns.
   * @returns {string} an SVG path `d` attribute.
   */
  function arc(from, to) {
    var a0 = from * 2 * Math.PI - Math.PI / 2;
    var a1 = to * 2 * Math.PI - Math.PI / 2;
    var big = to - from > 0.5 ? 1 : 0;
    var point = function (angle, radius) {
      return [
        CENTRE + radius * Math.cos(angle),
        CENTRE + radius * Math.sin(angle),
      ];
    };

    // A full ring cannot be one arc: SVG collapses a 360-degree arc to nothing,
    // so a single-slice donut would render blank. Two circles wound in opposite
    // directions, punched through with `fill-rule="evenodd"`, is the ring.
    if (to - from >= 0.9999) {
      return (
        "M" + (CENTRE - OUTER) + " " + CENTRE +
        "A" + OUTER + " " + OUTER + " 0 1 1 " + (CENTRE + OUTER) + " " + CENTRE +
        "A" + OUTER + " " + OUTER + " 0 1 1 " + (CENTRE - OUTER) + " " + CENTRE +
        "M" + (CENTRE - INNER) + " " + CENTRE +
        "A" + INNER + " " + INNER + " 0 1 0 " + (CENTRE + INNER) + " " + CENTRE +
        "A" + INNER + " " + INNER + " 0 1 0 " + (CENTRE - INNER) + " " + CENTRE
      );
    }

    var outerStart = point(a0, OUTER);
    var outerEnd = point(a1, OUTER);
    var innerEnd = point(a1, INNER);
    var innerStart = point(a0, INNER);
    return (
      "M" + outerStart[0] + " " + outerStart[1] +
      "A" + OUTER + " " + OUTER + " 0 " + big + " 1 " + outerEnd[0] + " " + outerEnd[1] +
      "L" + innerEnd[0] + " " + innerEnd[1] +
      "A" + INNER + " " + INNER + " 0 " + big + " 0 " + innerStart[0] + " " + innerStart[1] +
      "Z"
    );
  }

  /**
   * Create an SVG element with attributes set.
   *
   * @param {string} name - the tag name.
   * @param {Object} attrs - attribute name/value pairs.
   * @returns {Element} the new element.
   */
  function svg(name, attrs) {
    var node = document.createElementNS(SVG_NS, name);
    Object.keys(attrs).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  /**
   * Return the parts a chart is currently drawing.
   *
   * @param {Array} parts - every slice.
   * @param {Object} crossed - label to true, for the ones crossed out.
   * @returns {Array} the ones still counted.
   */
  function live(parts, crossed) {
    return parts.filter(function (part) {
      return !crossed[part.label];
    });
  }

  /**
   * Draw a chart's donut, centre readout and legend into `wrap`.
   *
   * Separate from :func:`chart` because it runs again on every press of a
   * legend key. Rebuilt rather than patched: a redraw is a dozen nodes, and the
   * alternative is arcs, tooltips, the readout and the legend each carrying
   * their own idea of what is showing.
   *
   * **The arcs re-normalise on what is left.** Crossing an asset out is the
   * reader saying "and what does the rest look like" -- the same question
   * design 1's chart answers, and the reason its legend is clickable at all.
   * A ring that kept a gap where the crossed slice was would answer a different
   * one.
   *
   * Built with `createElement` and `textContent`. Labels are asset and
   * collection names that came off the chain, and a unit is whatever its
   * creator typed -- the one place on this page where markup could be smuggled
   * in.
   *
   * @param {Element} wrap - the chart element.
   * @param {string} title - the chart's heading.
   * @param {Array} parts - every slice, crossed or not.
   * @param {number} scale - multiplier turning a slice value into ALGO.
   */
  function paint(wrap, title, parts, scale) {
    var crossed = wrap[CROSSED_PROP];
    var showing = live(parts, crossed);
    var span = showing.reduce(function (sum, part) {
      return sum + Math.abs(part.value);
    }, 0);
    var sum = showing.reduce(function (running, part) {
      return running + part.value;
    }, 0);

    wrap.textContent = "";

    var heading = document.createElement("h4");
    heading.textContent = title;
    wrap.appendChild(heading);

    var row = document.createElement("div");
    row.className = "chart-row";

    var ring = svg("svg", {
      class: "donut",
      viewBox: "0 0 120 120",
      role: "img",
      "aria-label": title + ": " + money(sum * scale) + " " + currency(),
    });

    var at = 0;
    showing.forEach(function (part) {
      var fraction = span ? Math.abs(part.value) / span : 0;
      if (!fraction) return;
      var path = svg("path", {
        d: arc(at, at + fraction),
        fill: part.color,
        "fill-rule": "evenodd",
      });
      var label = svg("title", {});
      label.textContent =
        part.label + " — " + (fraction * 100).toFixed(1) + "%";
      path.appendChild(label);
      ring.appendChild(path);
      at += fraction;
    });

    // The hole is where the figure goes. Design 1 puts this total in the
    // chart's title block; here the middle of the ring is both empty and
    // exactly where a reader looks, and it is what makes crossing a slice out
    // worth doing -- the number moves.
    var figure = svg("text", {
      class: "donut-total",
      x: CENTRE,
      y: CENTRE - 1,
      "text-anchor": "middle",
    });
    figure.textContent = money(sum * scale);
    ring.appendChild(figure);

    var unit = svg("text", {
      class: "donut-unit",
      x: CENTRE,
      y: CENTRE + 11,
      "text-anchor": "middle",
    });
    unit.textContent = currency();
    ring.appendChild(unit);

    row.appendChild(ring);

    var keys = document.createElement("div");
    keys.className = "keys";
    parts.forEach(function (part) {
      var off = Boolean(crossed[part.label]);

      // A real button, because it does something. It was a `<div>` carrying no
      // affordance at all, which is half of why these charts read as pictures
      // of design 1's rather than as the same control.
      var key = document.createElement("button");
      key.type = "button";
      key.className = "key" + (off ? " off" : "");
      key.style.color = part.color;
      key.setAttribute("aria-pressed", off ? "false" : "true");
      key.setAttribute(
        "aria-label",
        (off ? "Include " : "Exclude ") + part.label
      );
      key.setAttribute("data-key", part.label);

      var swatch = document.createElement("i");
      var name = document.createElement("span");
      name.className = "kn";
      name.textContent = part.label;
      var value = document.createElement("span");
      value.className = "kv num" + (part.value < 0 ? " neg" : "");
      value.textContent = money(part.value * scale);

      key.appendChild(swatch);
      key.appendChild(name);
      key.appendChild(value);
      keys.appendChild(key);
    });

    row.appendChild(keys);
    wrap.appendChild(row);
  }

  /**
   * Build one chart: a donut, its total and a legend that filters it.
   *
   * @param {string} title - the chart's heading.
   * @param {Array} parts - `[{label, value, color}]`.
   * @param {number} [scale] - multiplier turning a slice value into ALGO;
   *   1 when the values are already amounts.
   * @returns {Element|null} the chart element, or null if there is nothing.
   */
  function chart(title, parts, scale) {
    if (!parts.length) return null;

    var span = parts.reduce(function (sum, part) {
      return sum + Math.abs(part.value);
    }, 0);
    if (!span) return null;

    var wrap = document.createElement("div");
    wrap.className = "chart";
    // On the element rather than in a module-level map: five charts are on the
    // page and each crosses out its own labels, and a map keyed on a title
    // would have the assets chart and the collections chart sharing an entry
    // the moment two of them named the same thing.
    wrap[CROSSED_PROP] = {};
    wrap._asastatsParts = parts;
    wrap._asastatsScale = isFinite(scale) ? scale : 1;
    wrap._asastatsTitle = title;

    paint(wrap, title, parts, wrap._asastatsScale);
    return wrap;
  }

  /**
   * Cross one label out of its chart, or bring it back.
   *
   * @param {Element} key - the pressed legend button.
   */
  function toggleKey(key) {
    var wrap = key.closest(".chart");
    if (!wrap || !wrap[CROSSED_PROP] || !wrap._asastatsParts) return;

    var label = key.getAttribute("data-key");
    if (wrap[CROSSED_PROP][label]) {
      delete wrap[CROSSED_PROP][label];
    } else {
      wrap[CROSSED_PROP][label] = true;
    }
    paint(wrap, wrap._asastatsTitle, wrap._asastatsParts, wrap._asastatsScale);

    // The redraw replaced the button that was pressed, so focus has to be put
    // back on its replacement or a keyboard reader is returned to the top of
    // the document after every press. Matched by reading the attribute rather
    // than by building a selector from it: a label is an asset name off the
    // chain and may hold a quote.
    Array.prototype.forEach.call(
      wrap.querySelectorAll("[data-key]"),
      function (candidate) {
        if (candidate.getAttribute("data-key") === label) candidate.focus();
      }
    );
  }

  /**
   * Draw every chart into the grid, once.
   *
   * @param {Element} grid - the container.
   */
  function draw(grid) {
    if (grid.hasAttribute(BOUND_ATTR)) return;
    grid.setAttribute(BOUND_ATTR, "true");

    // The assets chart is the only payload naming every asset *and* carrying a
    // colour for each, so it is where a stacked payload borrows its colours.
    var assetColours = palette(payload("asachart"));

    var drawn = 0;
    CHARTS.forEach(function (spec) {
      var element = chart(
        spec.title,
        slices(payload(spec.id), assetColours),
        scaleFor(spec)
      );
      if (element) {
        // Which payload a chart was drawn from, so `redrawAllocation` can find
        // the one it is allowed to replace. Its heading is not the handle: that
        // is copy, and copy changes.
        element.setAttribute("data-chart", spec.id);
        grid.appendChild(element);
        drawn += 1;
      }
    });

    var note = document.getElementById("charts-note");
    if (note && !drawn) {
      note.textContent = "Nothing to chart for this address yet.";
    }
  }

  /**
   * Redraw the allocation donut from the toolbar's filtered totals.
   *
   * The bar, the five figures and this chart are three drawings of one set of
   * numbers, so when the toolbar filters a category out all three have to
   * follow. The other charts are of the whole address and are deliberately left
   * alone -- the same rule the headline follows: a reader who hides a category
   * has not stopped holding it.
   *
   * The category colours come from the stylesheet's `--c-*` custom properties
   * rather than from a table here, so the donut, the bar and the figures cannot
   * end up painting the same category two different colours.
   *
   * @param {object} totals - category key mapped to its filtered value.
   * @param {number} summed - the magnitudes' sum; nothing is drawn at zero.
   * @param {string} unit - the currency the values are in, for the legend.
   */
  function redrawAllocation(totals, summed, unit) {
    var grid = document.getElementById("charts-grid");
    if (!grid) return;
    var existing = grid.querySelector('[data-chart="ratiochart"]');
    if (!existing) return;

    var parts = Object.keys(totals)
      .filter(function (key) {
        return totals[key];
      })
      .map(function (key) {
        return {
          label: key.charAt(0).toUpperCase() + key.slice(1),
          value: totals[key],
          color: "var(--c-" + key + ")",
        };
      });

    // Scale 1: the toolbar hands over amounts, not shares.
    var replacement = summed ? chart("Allocation", parts, 1) : null;
    if (!replacement) {
      // Everything filtered out. The chart is emptied rather than removed, so
      // the panel keeps its shape and the chart comes back when the filter
      // does.
      existing.textContent = "";
      var note = document.createElement("h4");
      note.textContent = "Allocation";
      existing.appendChild(note);
      return;
    }
    replacement.setAttribute("data-chart", "ratiochart");
    if (unit) replacement.setAttribute("data-unit", unit);
    existing.parentNode.replaceChild(replacement, existing);
  }

  /**
   * Open or close one position's breakdown.
   *
   * The third level of the page: what the figure in the money column is made
   * of. `address.js` has a handler of the same name for design 1 and it does
   * not work here -- it toggles a `hidden` *class*, while this design hides the
   * panel with the `hidden` *attribute*, so the class went on and the panel
   * stayed shut. The control looked exactly right, dotted and inviting, and did
   * nothing; `functional_tests/test_address_dynamic_page.py` is what caught it.
   * `address.js` no longer binds to `.dynamic-page .tdist` for that reason.
   *
   * The control is a real button carrying `aria-expanded`, so the state is set
   * here too. Design 1's control is a span and has none, which is the other
   * half of why the two cannot share a handler.
   *
   * @param {Element} control - the pressed `.tdist` button.
   */
  function toggleBreakdown(control) {
    var panel = document.getElementById(control.getAttribute("data-distid"));
    if (!panel) return;

    panel.hidden = !panel.hidden;
    control.setAttribute("aria-expanded", panel.hidden ? "false" : "true");
  }

  /**
   * Fill every "N ago" span in the NFT section.
   *
   * `.epoch` is design 1's contract and the dynamic section keeps it, but
   * the *filling* could not be kept: `showTimes` is bound to
   * `.nft.item-header` and looks for `.item-body` siblings, and this design has
   * neither -- a collection is a `<details>` with a `.chead` and a `.cbody`. So
   * the section rendered "Last purchase on Rand Gallery" with no indication of
   * when, which reads as a rendering fault rather than as missing data.
   * `functional_tests/test_address_dynamic_nfts.py` is what noticed.
   *
   * Filled once on load rather than when a collection opens. Design 1 defers it
   * because its handler is per-collection; there is no handler here, and
   * formatting sixty-five intervals is not work worth deferring.
   *
   * `timeEntry` is `address.js`'s, which this page loads first, and is used so
   * the two designs word the same fact the same way. The fallback is a plain
   * date rather than nothing: a reader who is told a purchase happened is owed
   * when, and a script that failed to load is not their problem.
   *
   * @param {Document|Element} root - the subtree to fill. Required: every
   *   caller has one in hand, and a default would be a branch no test could
   *   reach.
   */
  function epochs(root) {
    var now = Date.now() / 1000;
    Array.prototype.forEach.call(
      root.querySelectorAll(".dynamic-page .epoch[data-epoch]"),
      function (element) {
        var at = parseInt(element.getAttribute("data-epoch"), 10);
        if (!isFinite(at)) return;
        element.textContent =
          typeof window.timeEntry === "function"
            ? window.timeEntry(now - at) + " ago"
            : new Date(at * 1000).toLocaleDateString();
      }
    );
  }

  /**
   * Bind the breakdown controls.
   *
   * Delegated from the document, so the rows `pins.js` moves -- and any that
   * arrive with an htmx partial -- need no rebinding. Guarded on the root
   * element for the same reason `showmore.js` guards there: this file can run
   * twice, and a second set of handlers would open and immediately close.
   */
  function breakdowns() {
    if (document.documentElement.hasAttribute(BREAKDOWN_ATTR)) return;
    document.documentElement.setAttribute(BREAKDOWN_ATTR, "true");

    document.addEventListener("click", function (event) {
      var control = event.target.closest
        ? event.target.closest(".tdist[data-distid]")
        : null;
      if (!control) return;
      toggleBreakdown(control);
    });

    // Legend keys, delegated for the same reason: a chart is built on first
    // open and rebuilt on every press, so there is no moment at which binding
    // to the buttons themselves would hold.
    document.addEventListener("click", function (event) {
      var key = event.target.closest
        ? event.target.closest(".chart .key[data-key]")
        : null;
      if (!key) return;
      toggleKey(key);
    });
  }

  /**
   * Bind the charts panel and the breakdown controls.
   *
   * The charts are drawn on first open rather than on load, and only once: the
   * payload does not change while the page is open, so redrawing on every
   * toggle would rebuild several hundred nodes to show the same picture.
   */
  function init() {
    breakdowns();
    epochs(document);

    var panel = document.getElementById("charts");
    var grid = document.getElementById("charts-grid");
    if (!panel || !grid || panel.hasAttribute(BOUND_ATTR)) return;
    panel.setAttribute(BOUND_ATTR, "true");

    // A `<details>` that arrives open -- restored by the browser, or opened
    // before this ran -- has no toggle coming.
    if (panel.open) draw(grid);
    panel.addEventListener("toggle", function () {
      if (panel.open) draw(grid);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for the jest suite, the way showmore.js and pins.js are. A
  // `typeof module !== "undefined"` guard would work too, but its false arm
  // cannot run under the test runner and would sit there uncovered forever.
  window.asastatsDynamic = {
    arc: arc,
    slices: slices,
    palette: palette,
    colorFor: colorFor,
    live: live,
    money: money,
    whole: whole,
    scaleFor: scaleFor,
    chart: chart,
    paint: paint,
    toggleKey: toggleKey,
    draw: draw,
    init: init,
    breakdowns: breakdowns,
    toggleBreakdown: toggleBreakdown,
    epochs: epochs,
    redrawAllocation: redrawAllocation,
  };
})();
