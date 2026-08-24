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

  /**
   * The six payload blocks, in the order they are drawn.
   *
   * `nftfloorchart` is deliberately last: it is the least-asked question on the
   * page, and a reader scanning left to right should meet the allocation and
   * the top assets first.
   */
  var CHARTS = [
    { id: "ratiochart", title: "Allocation" },
    { id: "distchart", title: "Top assets" },
    { id: "asachart", title: "Assets by value" },
    { id: "nftchart", title: "NFT collections" },
    { id: "nftfloorchart", title: "NFT floor value" },
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
   * Flatten a Chart.js-shaped payload into slices.
   *
   * @param {Object} data - `{labels, datasets: [{data, backgroundColor}]}`.
   * @returns {Array} `[{label, value, color}]`, empty if there is nothing.
   */
  function slices(data) {
    if (!data || !data.labels || !data.datasets || !data.datasets.length) {
      return [];
    }
    var set = data.datasets[0] || {};
    var values = set.data || [];
    var colors = set.backgroundColor || [];
    return data.labels
      .map(function (label, index) {
        return {
          label: String(label),
          value: parseFloat(values[index]) || 0,
          color: colors[index] || "currentColor",
        };
      })
      .filter(function (slice) {
        // Magnitude: a borrowed position is negative and cannot be drawn a
        // negative arc, but a zero slice is genuinely nothing to draw.
        return Math.abs(slice.value) > 0;
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
   * Render one chart: a donut and its legend.
   *
   * Built with `createElement` rather than an HTML string. Labels are asset and
   * collection names that came off the chain, and a unit is whatever its
   * creator typed -- the one place on this page where markup could be smuggled
   * in. `textContent` cannot be talked into parsing.
   *
   * @param {string} title - the chart's heading.
   * @param {Array} parts - `[{label, value, color}]`.
   * @returns {Element|null} the chart element, or null if there is nothing.
   */
  function chart(title, parts) {
    if (!parts.length) return null;

    var total = parts.reduce(function (sum, part) {
      return sum + Math.abs(part.value);
    }, 0);
    if (!total) return null;

    var wrap = document.createElement("div");
    wrap.className = "chart";

    var heading = document.createElement("h4");
    heading.textContent = title;
    wrap.appendChild(heading);

    var row = document.createElement("div");
    row.className = "chart-row";

    var ring = svg("svg", {
      class: "donut",
      viewBox: "0 0 120 120",
      role: "img",
      "aria-label": title,
    });

    var at = 0;
    parts.forEach(function (part) {
      var fraction = Math.abs(part.value) / total;
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

    row.appendChild(ring);

    var keys = document.createElement("div");
    keys.className = "keys";
    parts.forEach(function (part) {
      var key = document.createElement("div");
      key.className = "key";
      key.style.color = part.color;

      var swatch = document.createElement("i");
      var name = document.createElement("span");
      name.className = "kn";
      name.textContent = part.label;
      var value = document.createElement("span");
      value.className = "kv num" + (part.value < 0 ? " neg" : "");
      value.textContent = part.value.toFixed(2);

      key.appendChild(swatch);
      key.appendChild(name);
      key.appendChild(value);
      keys.appendChild(key);
    });

    row.appendChild(keys);
    wrap.appendChild(row);
    return wrap;
  }

  /**
   * Draw every chart into the grid, once.
   *
   * @param {Element} grid - the container.
   */
  function draw(grid) {
    if (grid.hasAttribute(BOUND_ATTR)) return;
    grid.setAttribute(BOUND_ATTR, "true");

    var drawn = 0;
    CHARTS.forEach(function (spec) {
      var element = chart(spec.title, slices(payload(spec.id)));
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

    var replacement = summed ? chart("Allocation", parts) : null;
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
    chart: chart,
    draw: draw,
    init: init,
    breakdowns: breakdowns,
    toggleBreakdown: toggleBreakdown,
    epochs: epochs,
    redrawAllocation: redrawAllocation,
  };
})();
