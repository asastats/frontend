/**
 * @jest-environment jsdom
 *
 * The money-column designs' charts, drawn as inline SVG.
 *
 * Design 1 keeps Chart.js and is not touched by any of this. What is worth
 * testing here is the arithmetic and the geometry -- a donut that renders
 * *something* looks fine in a browser while being quietly wrong, and the one
 * case that renders nothing at all (a single slice filling the ring) is
 * invisible until an address happens to hold exactly one thing.
 */

/** Load money.js against the current DOM and return what it exposes. */
function load() {
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/money.js")];
  require("../static/js/money.js");
  return window.asastatsMoney;
}

/**
 * Mount a `json_script` payload block.
 *
 * @param {string} id - the element id money.js looks for.
 * @param {object} data - the Chart.js-shaped payload.
 */
function mountPayload(id, data) {
  const node = document.createElement("script");
  node.type = "application/json";
  node.id = id;
  node.textContent = JSON.stringify(data);
  document.body.appendChild(node);
}

/** Mount the charts panel's containers. */
function mountPanel() {
  const panel = document.createElement("details");
  panel.id = "charts";
  const grid = document.createElement("div");
  grid.id = "charts-grid";
  const note = document.createElement("p");
  note.id = "charts-note";
  panel.appendChild(grid);
  panel.appendChild(note);
  document.body.appendChild(panel);
  return { panel, grid, note };
}

/** A payload with the given labels, values and colours. */
function chartData(labels, data, colors) {
  return { labels, datasets: [{ data, backgroundColor: colors }] };
}

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("arc geometry", () => {
  test("a partial slice draws a closed wedge", () => {
    const { arc } = load();

    const d = arc(0, 0.25);

    expect(d.startsWith("M")).toBe(true);
    expect(d.endsWith("Z")).toBe(true);
  });

  test("a slice under half a turn uses the small-arc flag", () => {
    const { arc } = load();

    expect(arc(0, 0.25)).toContain("0 0 1");
  });

  test("a slice over half a turn uses the large-arc flag", () => {
    // Without this a 70% slice renders as the 30% one, which is a picture that
    // looks entirely plausible and is the opposite of the truth.
    const { arc } = load();

    expect(arc(0, 0.7)).toContain("0 1 1");
  });

  test("a full ring is drawn as two circles, not one arc", () => {
    // SVG collapses a 360-degree arc to nothing. An address holding exactly one
    // thing would render a blank donut, and nothing would report an error.
    const { arc } = load();

    const d = arc(0, 1);

    expect(d).not.toContain("Z");
    expect(d.match(/A/g).length).toBe(4);
    expect(d.match(/M/g).length).toBe(2);
  });

  test("a very-nearly-full ring is treated as full", () => {
    // Floating-point shares of a total rarely land on exactly 1.
    const { arc } = load();

    expect(arc(0, 0.99995).match(/M/g).length).toBe(2);
  });

  test("slices start at twelve o'clock", () => {
    const { arc } = load();

    // The first point of a slice starting at 0 is directly above the centre.
    const [, y] = arc(0, 0.25).slice(1).split("A")[0].split(" ").map(Number);

    expect(y).toBeCloseTo(4);
  });
});

describe("reading a payload", () => {
  test("labels, values and colours are zipped into slices", () => {
    const { slices } = load();

    expect(slices(chartData(["A", "B"], [3, 7], ["#111", "#222"]))).toEqual([
      { label: "A", value: 3, color: "#111" },
      { label: "B", value: 7, color: "#222" },
    ]);
  });

  test("zero-valued entries are dropped", () => {
    // Nothing to draw, and a legend row for a holding of zero is noise.
    const { slices } = load();

    expect(slices(chartData(["A", "B"], [0, 7], ["#111", "#222"]))).toHaveLength(1);
  });

  test("a negative value survives, because a debt is not nothing", () => {
    const { slices } = load();

    expect(slices(chartData(["Borrowed"], [-4], ["#111"]))[0].value).toBe(-4);
  });

  test("a missing colour falls back rather than dropping the slice", () => {
    const { slices } = load();

    expect(slices(chartData(["A"], [1], []))[0].color).toBe("currentColor");
  });

  test("a payload with no datasets yields nothing", () => {
    const { slices } = load();

    expect(slices({ labels: ["A"] })).toEqual([]);
  });

  test("a null payload yields nothing", () => {
    const { slices } = load();

    expect(slices(null)).toEqual([]);
  });

  test("an unparseable value counts as zero and is dropped", () => {
    const { slices } = load();

    expect(slices(chartData(["A", "B"], ["nope", 5], ["#1", "#2"]))).toHaveLength(1);
  });
});

describe("building a chart", () => {
  test("one path per slice, each carrying a title", () => {
    // The title is what a screen reader and a hovering pointer both get. A
    // canvas offers neither, which is half the reason this is SVG.
    const { chart, slices } = load();

    const el = chart("Allocation", slices(chartData(["A", "B"], [1, 1], ["#1", "#2"])));

    expect(el.querySelectorAll("path")).toHaveLength(2);
    expect(el.querySelectorAll("title")).toHaveLength(2);
  });

  test("the title names the slice and its share", () => {
    const { chart, slices } = load();

    const el = chart("Allocation", slices(chartData(["A", "B"], [3, 1], ["#1", "#2"])));

    expect(el.querySelector("title").textContent).toBe("A — 75.0%");
  });

  test("shares are of magnitude, so a debt cannot invert the ring", () => {
    // Summing signed values would give a total smaller than its parts, and
    // fractions over 1 -- slices lapping the ring and painting over each other.
    const { chart, slices } = load();

    const el = chart("Mix", slices(chartData(["Held", "Owed"], [3, -1], ["#1", "#2"])));
    const shares = [...el.querySelectorAll("title")].map((t) => t.textContent);

    expect(shares).toEqual(["Held — 75.0%", "Owed — 25.0%"]);
  });

  test("the legend labels are text, never parsed as markup", () => {
    // Labels are asset names off the chain: whatever their creator typed.
    const { chart, slices } = load();

    const el = chart(
      "Assets",
      slices(chartData(["<img src=x onerror=alert(1)>"], [1], ["#1"])),
    );

    expect(el.querySelector("img")).toBeNull();
    expect(el.textContent).toContain("<img src=x onerror=alert(1)>");
  });

  test("a chart with nothing in it is not built", () => {
    const { chart } = load();

    expect(chart("Empty", [])).toBeNull();
  });

  test("a chart whose slices sum to zero is not built", () => {
    const { chart } = load();

    expect(chart("Zero", [{ label: "A", value: 0, color: "#1" }])).toBeNull();
  });

  test("the ring is labelled for a screen reader", () => {
    const { chart, slices } = load();

    const el = chart("Allocation", slices(chartData(["A"], [1], ["#1"])));

    expect(el.querySelector("svg").getAttribute("aria-label")).toBe("Allocation");
    expect(el.querySelector("svg").getAttribute("role")).toBe("img");
  });
});

describe("the panel", () => {
  test("nothing is drawn while the panel is closed", () => {
    // Six donuts of SVG is a lot of markup to hand a reader who never looks.
    const { grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));

    load().init();

    expect(grid.children.length).toBe(0);
  });

  test("opening the panel draws the charts", () => {
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A", "B"], [1, 2], ["#1", "#2"]));

    load().init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(1);
  });

  test("a panel that arrives open is drawn immediately", () => {
    // Restored by the browser, or opened before the script ran. There is no
    // toggle event coming, and waiting for one would leave it empty.
    const { panel, grid } = mountPanel();
    panel.open = true;
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));

    load().init();

    expect(grid.children.length).toBe(1);
  });

  test("charts are drawn once, not on every toggle", () => {
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));

    load().init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(1);
  });

  test("a second execution does not bind a second listener", () => {
    // The address page already pulls one script in through an htmx partial.
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));

    load().init();
    load().init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(1);
  });

  test("a malformed block costs its own chart, not the panel", () => {
    const { panel, grid } = mountPanel();
    const bad = document.createElement("script");
    // `type` matters: Django's `json_script` always emits it, and without it a
    // browser -- and jsdom -- treats the block as code and runs it.
    bad.type = "application/json";
    bad.id = "ratiochart";
    bad.textContent = "{not json";
    document.body.appendChild(bad);
    mountPayload("distchart", chartData(["A"], [1], ["#1"]));

    load().init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(1);
  });

  test("an address with nothing to chart is told so", () => {
    const { panel, note } = mountPanel();

    load().init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(note.textContent).toBe("Nothing to chart for this address yet.");
  });

  test("a page without the panel is left alone", () => {
    // Design 1 never loads this file, but a partial render might.
    expect(() => load().init()).not.toThrow();
  });
});

describe("when the script arrives before the document", () => {
  test("drawing waits for DOMContentLoaded", () => {
    // A deferred script runs after parsing, but this file is a plain <script>
    // in a block near the end of the page -- and the address page also pulls a
    // script in through an htmx partial, so the ordering is not guaranteed.
    const { panel, grid } = mountPanel();
    panel.open = true;
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));
    jest.spyOn(document, "readyState", "get").mockReturnValue("loading");

    load();

    expect(grid.children.length).toBe(0);

    document.dispatchEvent(new window.Event("DOMContentLoaded"));

    expect(grid.children.length).toBe(1);
  });
});

describe("payload shapes that are not charts", () => {
  // `slices` is the only thing standing between a malformed or empty payload
  // block and a TypeError inside the renderer. Each arm below is a shape the
  // six blocks can genuinely take: `_chart_setup` returns `labels: []` when an
  // address has nothing in a category, and a block can be absent entirely.

  test("a payload with no labels yields nothing", () => {
    const { slices } = load();

    expect(slices({ datasets: [{ data: [1] }] })).toEqual([]);
  });

  test("a payload with an empty datasets array yields nothing", () => {
    const { slices } = load();

    expect(slices({ labels: ["A"], datasets: [] })).toEqual([]);
  });

  test("a null first dataset yields nothing rather than throwing", () => {
    const { slices } = load();

    expect(slices({ labels: ["A"], datasets: [null] })).toEqual([]);
  });

  test("a dataset with no data array yields no drawable slices", () => {
    const { slices } = load();

    expect(slices({ labels: ["A"], datasets: [{}] })).toEqual([]);
  });

  test("a dataset with data but no colours still draws", () => {
    // The colours come from a separate map on the Django side; a payload that
    // lost them should still show the shape of the holding.
    const { slices } = load();

    expect(slices({ labels: ["A"], datasets: [{ data: [5] }] })).toEqual([
      { label: "A", value: 5, color: "currentColor" },
    ]);
  });

  test("an empty labels array yields nothing", () => {
    const { slices } = load();

    expect(slices({ labels: [], datasets: [{ data: [] }] })).toEqual([]);
  });
});

describe("closing the panel", () => {
  test("a toggle that closes the panel draws nothing", () => {
    // `toggle` fires on close as well as open. Without the `panel.open` check
    // this would call `draw` on the way out -- harmless today because `draw`
    // guards itself, but it would silently become a redraw the moment that
    // guard was relaxed for any other reason.
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));
    load().init();

    panel.open = false;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(0);
  });

  test("reopening after a close does not draw a second time", () => {
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["A"], [1], ["#1"]));
    load().init();

    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));
    panel.open = false;
    panel.dispatchEvent(new window.Event("toggle"));
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));

    expect(grid.children.length).toBe(1);
  });
});
