/**
 * @jest-environment jsdom
 *
 * The dynamic designs' charts, drawn as inline SVG.
 *
 * Design 1 keeps Chart.js and is not touched by any of this. What is worth
 * testing here is the arithmetic and the geometry -- a donut that renders
 * *something* looks fine in a browser while being quietly wrong, and the one
 * case that renders nothing at all (a single slice filling the ring) is
 * invisible until an address happens to hold exactly one thing.
 */

/** Load dynamic.js against the current DOM and return what it exposes. */
function load() {
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/dynamic.js")];
  require("../static/js/dynamic.js");
  return window.asastatsDynamic;
}

/**
 * Mount a `json_script` payload block.
 *
 * @param {string} id - the element id dynamic.js looks for.
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

describe("the breakdown controls", () => {
  /**
   * Mount one position row with a `.tdist` control and its panel.
   *
   * The panel is hidden with the `hidden` *attribute*, which is the shape the
   * dynamic template renders and the reason design 1's handler could
   * never open it -- that one toggles a `hidden` class, so it went on and the
   * panel stayed shut with the control reporting success.
   *
   * @param {string} id - the panel's id.
   * @returns {{control: Element, panel: Element}}
   */
  function mountBreakdown(id) {
    const control = document.createElement("button");
    control.type = "button";
    control.className = "amt tdist val";
    control.setAttribute("data-distid", id);
    control.setAttribute("aria-expanded", "false");

    const panel = document.createElement("div");
    panel.id = id;
    panel.className = "dist";
    panel.hidden = true;

    document.body.appendChild(control);
    document.body.appendChild(panel);
    return { control, panel };
  }

  test("pressing the control opens the breakdown and says so", () => {
    const money = load();
    money.init();
    const { control, panel } = mountBreakdown("dist-1-abc");

    control.click();

    expect(panel.hidden).toBe(false);
    expect(control.getAttribute("aria-expanded")).toBe("true");
  });

  test("pressing it again closes the breakdown", () => {
    const money = load();
    money.init();
    const { control, panel } = mountBreakdown("dist-1-def");

    control.click();
    control.click();

    expect(panel.hidden).toBe(true);
    expect(control.getAttribute("aria-expanded")).toBe("false");
  });

  test("pressing something inside the control still opens it", () => {
    // The control carries an icon in the page; a click lands on the child, and
    // `closest` is what walks back up to the button that owns the state.
    const money = load();
    money.init();
    const { control, panel } = mountBreakdown("dist-1-ghi");
    const inner = document.createElement("span");
    control.appendChild(inner);

    inner.click();

    expect(panel.hidden).toBe(false);
  });

  test("a click on anything else is left alone", () => {
    const money = load();
    money.init();
    const { panel } = mountBreakdown("dist-1-jkl");
    const elsewhere = document.createElement("div");
    document.body.appendChild(elsewhere);

    elsewhere.click();

    expect(panel.hidden).toBe(true);
  });

  test("a click whose target cannot be walked up from is ignored", () => {
    // `document` is a legitimate event target and has no `closest`. Reached in
    // a browser by a programmatic dispatch, and it must not throw -- this
    // handler sits on every click the page receives.
    const money = load();
    money.init();

    expect(() =>
      document.dispatchEvent(new window.Event("click", { bubbles: true })),
    ).not.toThrow();
  });

  test("a control pointing at no panel does nothing rather than throwing", () => {
    // A stale `data-distid` -- a breakdown that stopped being rendered while
    // the control stayed. Silent is right here: there is nothing to show and
    // nothing a reader could do about it.
    const money = load();
    const orphan = document.createElement("button");
    orphan.className = "tdist";
    orphan.setAttribute("data-distid", "dist-nothing-here");
    orphan.setAttribute("aria-expanded", "false");
    document.body.appendChild(orphan);

    expect(() => money.toggleBreakdown(orphan)).not.toThrow();
    expect(orphan.getAttribute("aria-expanded")).toBe("false");
  });

  test("a second binding does not open and immediately close", () => {
    // The failure this guards against is silent: two delegated handlers toggle
    // twice per click and the control simply looks dead. `pins.js` and
    // `showmore.js` guard the same way and for the same reason -- an htmx
    // partial on this page can run the file again.
    const money = load();
    money.init();
    money.breakdowns();
    money.breakdowns();
    const { control, panel } = mountBreakdown("dist-1-mno");

    control.click();

    expect(panel.hidden).toBe(false);
  });
});

describe("redrawing the allocation from a filtered view", () => {
  /**
   * The bar, the five figures and this donut are three drawings of one set of
   * numbers, so when the toolbar filters a category out all three follow. The
   * other charts are of the whole address and are deliberately left alone --
   * the same rule the headline follows.
   */
  function openPanel() {
    const { panel, grid } = mountPanel();
    mountPayload("ratiochart", chartData(["Balance", "Staked"], [60, 40], ["#1", "#2"]));
    mountPayload("distchart", chartData(["A"], [5], ["#3"]));
    const money = load();
    money.init();
    panel.open = true;
    panel.dispatchEvent(new window.Event("toggle"));
    return { grid, money };
  }

  test("the allocation chart is replaced with the filtered one", () => {
    const { grid, money } = openPanel();

    money.redrawAllocation({ balance: 10, staked: 90 }, 100, "ALGO");

    const chart = grid.querySelector('[data-chart="ratiochart"]');
    expect(chart.querySelectorAll("path")).toHaveLength(2);
    expect(chart.querySelector(".kv").textContent).toBe("10.00");
  });

  test("the other charts are left alone", () => {
    const { grid, money } = openPanel();
    const before = grid.querySelector('[data-chart="distchart"]');

    money.redrawAllocation({ balance: 10 }, 10, "ALGO");

    expect(grid.querySelector('[data-chart="distchart"]')).toBe(before);
  });

  test("a category filtered to nothing is left out of the ring", () => {
    const { grid, money } = openPanel();

    money.redrawAllocation({ balance: 10, staked: 0 }, 10, "ALGO");

    expect(grid.querySelector('[data-chart="ratiochart"]').querySelectorAll("path")).toHaveLength(1);
  });

  test("everything filtered out empties the chart rather than removing it", () => {
    // The panel keeps its shape, and the chart comes back when the filter does.
    const { grid, money } = openPanel();

    money.redrawAllocation({ balance: 0, staked: 0 }, 0, "ALGO");

    const chart = grid.querySelector('[data-chart="ratiochart"]');
    expect(chart).not.toBeNull();
    expect(chart.querySelectorAll("path")).toHaveLength(0);
    expect(chart.querySelector("h4").textContent).toBe("Allocation");
  });

  test("the currency it was drawn in is recorded on the chart", () => {
    const { grid, money } = openPanel();

    money.redrawAllocation({ balance: 10 }, 10, "USD");

    expect(grid.querySelector('[data-chart="ratiochart"]').getAttribute("data-unit")).toBe("USD");
  });

  test("no currency leaves the chart unlabelled rather than blank-labelled", () => {
    const { grid, money } = openPanel();

    money.redrawAllocation({ balance: 10 }, 10, "");

    expect(grid.querySelector('[data-chart="ratiochart"]').hasAttribute("data-unit")).toBe(false);
  });

  test("a page with no charts grid is left alone", () => {
    const money = load();

    expect(() => money.redrawAllocation({ balance: 1 }, 1, "ALGO")).not.toThrow();
  });

  test("a panel that was never drawn has no allocation chart to replace", () => {
    mountPanel();
    const money = load();

    expect(() => money.redrawAllocation({ balance: 1 }, 1, "ALGO")).not.toThrow();
  });
});

describe("dating the NFT purchases", () => {
  /**
   * `.epoch` is design 1's contract and the dynamic NFT section keeps it,
   * but the filling could not be kept: `showTimes` binds to `.nft.item-header`
   * and looks for `.item-body` siblings, and this design has neither. So the
   * section said "Last purchase on Rand Gallery" with no indication of when.
   */
  function mountEpoch(seconds) {
    const page = document.createElement("div");
    page.className = "dynamic-page";
    const span = document.createElement("span");
    span.className = "epoch";
    span.setAttribute("data-epoch", String(seconds));
    page.appendChild(span);
    document.body.appendChild(page);
    return span;
  }

  afterEach(() => {
    delete window.timeEntry;
  });

  test("an interval is worded the way design 1 words it", () => {
    // Both designs describe the same fact, so they use the same formatter --
    // `address.js`'s, which this page loads first.
    window.timeEntry = (interval) => `${Math.round(interval / 86400)} days`;
    const span = mountEpoch(Math.floor(Date.now() / 1000) - 86400 * 3);

    load().epochs(document);

    expect(span.textContent).toBe("3 days ago");
  });

  test("without that formatter a plain date is still shown", () => {
    // A reader told a purchase happened is owed when. A script that failed to
    // load is not their problem, and an empty span reads as a rendering fault
    // rather than as missing data.
    const span = mountEpoch(1691625566);

    load().epochs(document);

    expect(span.textContent).not.toBe("");
    expect(Number.isNaN(Date.parse(span.textContent))).toBe(false);
  });

  test("an epoch that is not a number is left alone", () => {
    const span = mountEpoch("whenever");

    load().epochs(document);

    expect(span.textContent).toBe("");
  });

  test("it fills every span on the page, not only the first", () => {
    window.timeEntry = () => "2 days";
    const first = mountEpoch(1691625566);
    const second = mountEpoch(1691625566);

    load().epochs(document);

    expect(first.textContent).toBe("2 days ago");
    expect(second.textContent).toBe("2 days ago");
  });

  test("a subtree can be filled on its own", () => {
    window.timeEntry = () => "1 day";
    mountEpoch(1691625566);
    const scoped = document.createElement("div");
    document.body.appendChild(scoped);

    load().epochs(scoped);

    expect(document.querySelector(".epoch").textContent).toBe("");
  });

  test("init fills them without being asked", () => {
    window.timeEntry = () => "5 days";
    const span = mountEpoch(1691625566);

    load().init();

    expect(span.textContent).toBe("5 days ago");
  });
});
