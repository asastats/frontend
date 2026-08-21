/**
 * @jest-environment jsdom
 *
 * Pinning a position, and the fallback that makes it possible at all.
 *
 * Three pids in the reference bundle name two rows each -- two Lofty AMM
 * entries, two Cometa stakes, two Gora.fi delegations -- because every
 * identifying field the payload carries is identical for both. Only the value
 * and the amount differ, and those are the two things that change between
 * loads.
 *
 * The captured fixture is a three-asset trim and contains none of them, so the
 * ambiguous cases are built here by hand. The unambiguous ones are checked
 * against the fixture in pins.test.js's company; what matters in this file is
 * what happens when a pid is not enough.
 */

/**
 * Build one asset's position list.
 *
 * @param {object[]} positions - `{pid, amount, ambiguous}` per row.
 * @param {string} id - the container's id, for addressing it afterwards.
 * @returns {Element} the `[data-positions]` container.
 */
function mountPositions(positions, id = "asset-a") {
  const container = document.createElement("div");
  container.setAttribute("data-positions", "");
  container.id = id;

  positions.forEach((spec, index) => {
    const position = document.createElement("div");
    position.className = "position";
    position.dataset.pid = spec.pid;
    position.dataset.amount = spec.amount === undefined ? "" : String(spec.amount);
    if (spec.ambiguous) position.setAttribute("data-pid-ambiguous", "");
    position.dataset.testid = `${id}-${index}`;

    const summary = document.createElement("div");
    summary.className = "position-row";
    summary.innerHTML =
      `<span class="position-label">${spec.label || spec.pid}</span>` +
      `<span class="amt">${spec.value === undefined ? "" : spec.value}</span>` +
      `<button type="button" class="pin-btn" ` +
      `data-pin-position="${spec.pid}" aria-pressed="false"></button>`;
    position.appendChild(summary);
    container.appendChild(position);
  });

  document.body.appendChild(container);
  return container;
}

/** Load pins.js against the current DOM. */
function load() {
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/pins.js")];
  require("../static/js/pins.js");
  return window.asastatsPins;
}

/** Test ids of a container's positions, in document order. */
function orderOf(container) {
  return Array.from(container.children).map((el) => el.dataset.testid);
}

/** The control inside the position at `index` of `container`. */
function controlAt(container, index) {
  return container.children[index].querySelector("[data-pin-position]");
}

beforeEach(() => {
  localStorage.clear();
  document.body.innerHTML = "";
  Object.defineProperty(document, "readyState", {
    value: "complete",
    configurable: true,
  });
  window.history.pushState({}, "", "/VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU");
});

describe("an unambiguous position", () => {
  test("pinning floats it to the top of its asset", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
      { pid: "p1-a-3", amount: 30 },
    ]);
    const pins = load();

    pins.togglePosition(controlAt(container, 2), document);

    expect(orderOf(container)[0]).toBe("asset-a-2");
  });

  test("the rest keep the order the server sent", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
      { pid: "p1-a-3", amount: 30 },
    ]);
    const pins = load();

    pins.togglePosition(controlAt(container, 2), document);

    expect(orderOf(container).slice(1)).toEqual(["asset-a-0", "asset-a-1"]);
  });

  test("unpinning puts it back", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    const pins = load();
    const served = orderOf(container);

    pins.togglePosition(controlAt(container, 1), document);
    pins.togglePosition(controlAt(container, 0), document);

    expect(orderOf(container)).toEqual(served);
  });

  test("it survives a reload", () => {
    mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    let pins = load();
    pins.togglePosition(controlAt(document.getElementById("asset-a"), 1), document);

    document.body.innerHTML = "";
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    pins = load();

    // The pinned row is the one served second, so after restoration the top of
    // the list is the row that was rendered at index 1.
    expect(orderOf(container)[0]).toBe("asset-a-1");
    expect(container.children[0].dataset.pid).toBe("p1-a-2");
  });

  test("the control reports its state", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    const pins = load();

    pins.togglePosition(controlAt(container, 1), document);

    expect(controlAt(container, 0).getAttribute("aria-pressed")).toBe("true");
    expect(container.children[0].classList.contains("pinned")).toBe(true);
  });
});

describe("two positions sharing a pid", () => {
  /** The Cometa case: same everything, two amounts. */
  function mountAmbiguous(first = 5000000000, second = 3500000000) {
    return mountPositions([
      { pid: "p1-393537671-62fc21", amount: first, ambiguous: true },
      { pid: "p1-393537671-62fc21", amount: second, ambiguous: true },
    ]);
  }

  test("pinning the second restores the second, not the first", () => {
    // The whole point. Without the amount witness both rows answer to the same
    // name and the reader's choice is a coin toss on every reload.
    mountAmbiguous();
    let pins = load();
    pins.togglePosition(controlAt(document.getElementById("asset-a"), 1), document);

    document.body.innerHTML = "";
    const container = mountAmbiguous();
    pins = load();

    expect(container.children[0].dataset.amount).toBe("3500000000");
  });

  test("pinning the first restores the first", () => {
    mountAmbiguous();
    let pins = load();
    pins.togglePosition(controlAt(document.getElementById("asset-a"), 0), document);

    document.body.innerHTML = "";
    const container = mountAmbiguous();
    pins = load();

    expect(container.children[0].dataset.amount).toBe("5000000000");
  });

  test("a drifted amount still finds its row", () => {
    // Staking rewards accrue, so the amount moves a little between visits. The
    // nearest match is what makes the witness usable rather than brittle.
    mountAmbiguous();
    let pins = load();
    pins.togglePosition(controlAt(document.getElementById("asset-a"), 1), document);

    document.body.innerHTML = "";
    const container = mountAmbiguous(5100000000, 3510000000);
    pins = load();

    expect(container.children[0].dataset.amount).toBe("3510000000");
  });

  test("only one of the two is marked as pinned", () => {
    const container = mountAmbiguous();
    const pins = load();

    pins.togglePosition(controlAt(container, 1), document);

    const pinned = Array.from(container.children).filter((el) =>
      el.classList.contains("pinned"),
    );
    expect(pinned).toHaveLength(1);
  });

  test("unpinning removes exactly one pin", () => {
    const container = mountAmbiguous();
    const pins = load();

    pins.togglePosition(controlAt(container, 1), document);
    pins.togglePosition(controlAt(container, 0), document);

    expect(pins.readPositions()).toHaveLength(0);
  });

  test("both can be pinned at once", () => {
    const container = mountAmbiguous();
    const pins = load();

    pins.togglePosition(controlAt(container, 0), document);
    pins.togglePosition(controlAt(container, 1), document);

    expect(pins.readPositions()).toHaveLength(2);
  });

  test("amounts that cross pick the wrong row, and that is the known cost", () => {
    // Documented rather than hidden. The ordinal alternative fails on *any*
    // reordering; this needs the two amounts to actually swap magnitude, and
    // the row carries `data-pid-ambiguous` so the page can say so.
    mountAmbiguous(5000000000, 3500000000);
    let pins = load();
    pins.togglePosition(controlAt(document.getElementById("asset-a"), 1), document);

    document.body.innerHTML = "";
    // The reader moved most of their stake from one to the other.
    const container = mountAmbiguous(3400000000, 5100000000);
    pins = load();

    expect(container.children[0].dataset.amount).toBe("3400000000");
  });
});

describe("resolution edge cases", () => {
  test("a pid that is no longer on the page is skipped", () => {
    const container = mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const pins = load();
    pins.writePositions([{ pid: "p1-gone", amount: 5 }, { pid: "p1-a-1", amount: 10 }]);

    pins.applyPositions(document);

    expect(container.children[0].classList.contains("pinned")).toBe(true);
  });

  test("a stored pin with no amount falls back to the first match", () => {
    const container = mountPositions([
      { pid: "p1-dup", amount: 10, ambiguous: true },
      { pid: "p1-dup", amount: 20, ambiguous: true },
    ]);
    const pins = load();
    pins.writePositions([{ pid: "p1-dup", amount: "" }]);

    pins.applyPositions(document);

    expect(container.children[0].dataset.amount).toBe("10");
  });

  test("a row with no amount is not chosen over one that has it", () => {
    const container = mountPositions([
      { pid: "p1-dup", amount: undefined, ambiguous: true },
      { pid: "p1-dup", amount: 20, ambiguous: true },
    ]);
    const pins = load();
    pins.writePositions([{ pid: "p1-dup", amount: 20 }]);

    pins.applyPositions(document);

    expect(container.children[0].dataset.amount).toBe("20");
  });

  test("malformed storage reads as no pins", () => {
    const pins = load();
    localStorage.setItem(pins.positionsKey(), "{not json");

    expect(pins.readPositions()).toEqual([]);
  });

  test("entries without a pid are dropped", () => {
    const pins = load();
    localStorage.setItem(pins.positionsKey(), '[{"amount": 1}, {"pid": "p1-a"}]');

    expect(pins.readPositions()).toEqual([{ pid: "p1-a" }]);
  });

  test("resolve returns null when nothing matches", () => {
    mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const pins = load();

    expect(pins.resolve({ pid: "p1-nope", amount: 1 }, document)).toBeNull();
  });

  test("falls back to first candidate when all candidates have non-numeric amounts", () => {
    const container = mountPositions([
      { pid: "p1-dup", amount: "not-a-number", ambiguous: true },
      { pid: "p1-dup", amount: "also-not-a-number", ambiguous: true },
    ]);
    const pins = load();

    const resolved = pins.resolve({ pid: "p1-dup", amount: 10 }, document);
    expect(resolved).toBe(container.children[0]);
  });

  test("skips layoutPositions when parent has no served entries", () => {
    const container = mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const pins = load();
    Object.defineProperty(container, "_asastatsServedEntries", {
      get: () => undefined,
      set: () => {},
      configurable: true,
    });

    expect(() => pins.applyPositions(document)).not.toThrow();
  });

  test("handles control outside a position element gracefully", () => {
    const stray = document.createElement("button");
    stray.setAttribute("data-pin-position", "p1-stray");
    document.body.appendChild(stray);

    const pins = load();

    expect(() => pins.togglePosition(stray, document)).not.toThrow();
    expect(stray.getAttribute("aria-pressed")).toBe("false");
  });
});

describe("two assets", () => {
  test("a pin moves a position only within its own asset", () => {
    const first = mountPositions(
      [{ pid: "p1-a-1", amount: 10 }, { pid: "p1-a-2", amount: 20 }],
      "asset-a",
    );
    const second = mountPositions(
      [{ pid: "p1-b-1", amount: 30 }, { pid: "p1-b-2", amount: 40 }],
      "asset-b",
    );
    const pins = load();
    const servedSecond = orderOf(second);

    pins.togglePosition(controlAt(first, 1), document);

    expect(orderOf(first)[0]).toBe("asset-a-1");
    expect(orderOf(second)).toEqual(servedSecond);
  });

  test("each asset keeps its own pinned position at its own top", () => {
    const first = mountPositions(
      [{ pid: "p1-a-1", amount: 10 }, { pid: "p1-a-2", amount: 20 }],
      "asset-a",
    );
    const second = mountPositions(
      [{ pid: "p1-b-1", amount: 30 }, { pid: "p1-b-2", amount: 40 }],
      "asset-b",
    );
    const pins = load();

    pins.togglePosition(controlAt(first, 1), document);
    pins.togglePosition(controlAt(second, 1), document);

    expect(orderOf(first)[0]).toBe("asset-a-1");
    expect(orderOf(second)[0]).toBe("asset-b-1");
  });
});

describe("clicking the control", () => {
  test("pins without toggling the panel it sits in", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });

    controlAt(container, 1).dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
    expect(orderOf(container)[0]).toBe("asset-a-1");
  });

  test("clicking elsewhere does not trigger position toggle", () => {
    mountPositions([
      { pid: "p1-a-1", amount: 10 },
      { pid: "p1-a-2", amount: 20 },
    ]);
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });

    document.body.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
  });
});

/**
 * Mount the pinned band's containers.
 *
 * The band is rendered empty by the server and filled here, because the address
 * page's cache entry is shared between readers on a layout and one reader's
 * pins are not another's.
 *
 * @returns {object} the section, grid and count elements.
 */
function mountBand() {
  const section = document.createElement("section");
  section.id = "pinned-section";
  section.hidden = true;
  const grid = document.createElement("div");
  grid.id = "pin-grid";
  const count = document.createElement("span");
  count.id = "pin-count";
  section.appendChild(count);
  section.appendChild(grid);
  document.body.appendChild(section);
  return { section, grid, count };
}

describe("the pinned band", () => {
  test("stays hidden while nothing is pinned", () => {
    mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const { section, grid } = mountBand();

    load();

    expect(section.hidden).toBe(true);
    expect(grid.children.length).toBe(0);
  });

  test("appears with a card once a position is pinned", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10, label: "Tinyman2 LP", value: "12.50" },
    ]);
    const { section, grid, count } = mountBand();
    const api = load();

    api.togglePosition(controlAt(container, 0), document);

    expect(section.hidden).toBe(false);
    expect(grid.children.length).toBe(1);
    expect(grid.textContent).toContain("Tinyman2 LP");
    expect(count.textContent).toBe("1");
  });

  test("a lone position can be pinned, and lands in the band", () => {
    // The case the design contract used to forbid. Floating a row within a
    // group of one changes nothing; copying it to the top of the page does not.
    const container = mountPositions([
      { pid: "p1-solo", amount: 5, label: "Folks deposit" },
    ]);
    const { grid } = mountBand();
    const api = load();

    api.togglePosition(controlAt(container, 0), document);

    expect(grid.children.length).toBe(1);
    expect(grid.textContent).toContain("Folks deposit");
  });

  test("the row itself stays where it was", () => {
    // The band holds copies. Moving the row out of its asset would take it away
    // from the money column it aligns to and the subtotal it contributes to.
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10, label: "One" },
      { pid: "p1-a-2", amount: 20, label: "Two" },
    ]);
    mountBand();
    const api = load();

    api.togglePosition(controlAt(container, 1), document);

    expect(container.querySelectorAll(".position").length).toBe(2);
  });

  test("a pin that resolves to nothing keeps a stale card", () => {
    // Silently dropping it would tell the reader nothing about why the thing
    // they pinned vanished -- and it may only be inside a folded tail.
    mountPositions([{ pid: "p1-present", amount: 1 }]);
    const { grid } = mountBand();
    const api = load();
    api.writePositions([{ pid: "p1-gone", amount: 3, label: "Closed stake" }]);

    api.applyPositions(document);

    expect(grid.children.length).toBe(1);
    expect(grid.firstChild.classList.contains("stale")).toBe(true);
    expect(grid.textContent).toContain("Closed stake");
  });

  test("a stale card falls back to the pid when no label was stored", () => {
    mountPositions([{ pid: "p1-present", amount: 1 }]);
    const { grid } = mountBand();
    const api = load();
    api.writePositions([{ pid: "p1-gone", amount: 3 }]);

    api.applyPositions(document);

    expect(grid.textContent).toContain("p1-gone");
  });

  test("a card marks itself ambiguous when the pid names more than one row", () => {
    const container = mountPositions([
      { pid: "p1-dup", amount: 11, ambiguous: true, label: "Lofty AMM" },
      { pid: "p1-dup", amount: 1, ambiguous: true, label: "Lofty AMM" },
    ]);
    const { grid } = mountBand();
    const api = load();

    api.togglePosition(controlAt(container, 0), document);

    expect(grid.firstChild.classList.contains("ambiguous")).toBe(true);
  });

  test("the band's remove control unpins", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10, label: "One" },
    ]);
    const { section, grid } = mountBand();
    const api = load();
    api.togglePosition(controlAt(container, 0), document);

    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    grid.querySelector("[data-unpin-position]").dispatchEvent(event);

    expect(api.readPositions()).toEqual([]);
    expect(section.hidden).toBe(true);
  });

  test("removing works for a stale card, which has no row to point at", () => {
    // Why `unpinPosition` takes a pid rather than a row: this is the main case.
    mountPositions([{ pid: "p1-present", amount: 1 }]);
    const { grid } = mountBand();
    const api = load();
    api.writePositions([{ pid: "p1-gone", amount: 3, label: "Closed" }]);
    api.applyPositions(document);

    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    grid.querySelector("[data-unpin-position]").dispatchEvent(event);

    expect(api.readPositions()).toEqual([]);
  });

  test("cards are built as elements, never parsed from a string", () => {
    // Card text is asset and venue names that came off the chain. This is the
    // one place on the page markup could be smuggled in.
    mountPositions([{ pid: "p1-x", amount: 1 }]);
    const { grid } = mountBand();
    const api = load();
    api.writePositions([
      { pid: "p1-x-gone", amount: 1, label: "<img src=x onerror=alert(1)>" },
    ]);

    api.applyPositions(document);

    expect(grid.querySelector("img")).toBeNull();
    expect(grid.textContent).toContain("<img src=x onerror=alert(1)>");
  });

  test("a page with no band is left alone", () => {
    // Design 1 has no band, and pins.js is not loaded there -- but the historic
    // widget renders positions without one, so this must not throw.
    const container = mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const api = load();

    expect(() => api.togglePosition(controlAt(container, 0), document)).not.toThrow();
  });

  test("the band re-renders rather than accumulating", () => {
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10, label: "One" },
    ]);
    const { grid } = mountBand();
    const api = load();

    api.togglePosition(controlAt(container, 0), document);
    api.applyPositions(document);
    api.applyPositions(document);

    expect(grid.children.length).toBe(1);
  });
});

describe("band cards built from unfamiliar markup", () => {
  /**
   * Mount a position carrying only its identity.
   *
   * The historic widget renders positions without the address page's chrome,
   * and a card built from one must still name something rather than throwing
   * on a missing element.
   *
   * @param {string} pid - the position's identity.
   * @returns {Element} the container.
   */
  function mountBare(pid) {
    const container = document.createElement("div");
    container.setAttribute("data-positions", "");
    const position = document.createElement("div");
    position.className = "position";
    position.dataset.pid = pid;
    position.dataset.amount = "1";
    position.innerHTML =
      `<button type="button" class="pin-btn" data-pin-position="${pid}"></button>`;
    container.appendChild(position);
    document.body.appendChild(container);
    return container;
  }

  test("a position with no label falls back to its identity", () => {
    const container = mountBare("p1-bare");
    const { grid } = mountBand();
    const api = load();

    api.togglePosition(container.querySelector("[data-pin-position]"), document);

    expect(grid.textContent).toContain("p1-bare");
  });

  test("a position with no figure yields a card with no value", () => {
    const container = mountBare("p1-bare");
    const { grid } = mountBand();
    const api = load();

    api.togglePosition(container.querySelector("[data-pin-position]"), document);

    expect(grid.querySelector(".amt").textContent).toBe("");
  });

  test("nothing is stored as the label when there is none to store", () => {
    const container = mountBare("p1-bare");
    mountBand();
    const api = load();

    api.togglePosition(container.querySelector("[data-pin-position]"), document);

    expect(api.readPositions()[0].label).toBe("");
  });
});

describe("a band without a counter", () => {
  test("renders its cards and does not throw", () => {
    // `#pin-count` is optional: a narrow or compact layout may show the band
    // without a running total. The section and the grid are not optional --
    // without either there is nowhere to put a card, and `renderBand` returns.
    const container = mountPositions([
      { pid: "p1-a-1", amount: 10, label: "One" },
    ]);
    const section = document.createElement("section");
    section.id = "pinned-section";
    section.hidden = true;
    const grid = document.createElement("div");
    grid.id = "pin-grid";
    section.appendChild(grid);
    document.body.appendChild(section);
    const api = load();

    api.togglePosition(controlAt(container, 0), document);

    expect(grid.children.length).toBe(1);
    expect(section.hidden).toBe(false);
  });

  test("a page with a grid but no section leaves both alone", () => {
    const container = mountPositions([{ pid: "p1-a-1", amount: 10 }]);
    const grid = document.createElement("div");
    grid.id = "pin-grid";
    document.body.appendChild(grid);
    const api = load();

    api.togglePosition(controlAt(container, 0), document);

    expect(grid.children.length).toBe(0);
  });
});
