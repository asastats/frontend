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
    summary.className = "position-summary";
    summary.innerHTML =
      `<button type="button" class="pin pin-position" ` +
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
