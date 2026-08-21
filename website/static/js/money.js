/**
 * @file Charts for the money-column address designs, drawn as inline SVG.
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
  var BOUND_ATTR = "data-money-bound";

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
   * Bind the charts panel.
   *
   * Drawn on first open rather than on load, and only once: the payload does
   * not change while the page is open, so redrawing on every toggle would
   * rebuild several hundred nodes to show the same picture.
   */
  function init() {
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
  window.asastatsMoney = {
    arc: arc,
    slices: slices,
    chart: chart,
    draw: draw,
    init: init,
  };
})();
