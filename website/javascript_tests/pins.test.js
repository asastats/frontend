/**
 * @jest-environment jsdom
 */

/** Entry ids the mounted page offers a pin control for. */
const ASSET = "f393401013";
const ALGO = "f0";
const COLLECTION = "fknith3ds";

/**
 * The entries a mounted page carries: three assets, then two collections.
 *
 * Ids and order match what the captured fixture used to provide, so every
 * assertion below is unchanged from when this file read `address.html`.
 */
const ASSETS = [ASSET, ALGO, "f246516580"];
const COLLECTIONS = [COLLECTION, "fbrave-new-world"];

/**
 * Build one section of entries, each with a grip and a pin.
 *
 * Synthetic rather than the captured address page, since 2026-08-20: pinning
 * and reordering belong to the money-column designs, and design 1 -- which is
 * what `address.html` captures -- deliberately carries neither. Reading the
 * fixture would tie these tests to whichever design happens to ship the
 * controls, which is not what any of them is about.
 *
 * The shape is the part that matters and is reproduced exactly: entries are
 * `.fitem` with a unique id, siblings inside one container, inside a section.
 *
 * @param {string} section - "asasec" or "nftsec".
 * @param {string[]} ids - entry ids in served order.
 * @param {boolean} nested - give each entry a nested `.fitem` child, as an NFT
 *   collection has one per item.
 */
function mountSection(section, ids, nested) {
  const wrap = document.createElement("div");
  wrap.className = `${section} section-list`;
  const rows = document.createElement("div");

  ids.forEach((id) => {
    const entry = document.createElement("details");
    entry.className = "fitem";
    entry.id = id;
    entry.innerHTML =
      '<summary class="item-header"><span class="itemleft">' +
      '<span class="entry-controls">' +
      `<button type="button" class="grip" data-drag="${id}"></button>` +
      `<button type="button" class="pin" data-pin="${id}" aria-pressed="false"></button>` +
      "</span></span></summary>" +
      (nested ? `<div class="item-body"><div class="fitem" id="i${id}"></div></div>` : "");
    rows.appendChild(entry);
  });

  wrap.appendChild(rows);
  document.body.appendChild(wrap);
}

/**
 * Mount a page carrying both sections and load pins.js against it.
 *
 * The module is an IIFE that arranges the page as it loads, so it has to be
 * required *after* the DOM exists and re-required for every test -- hence the
 * cache eviction rather than a plain require at the top of the file.
 *
 * @returns {object} the `window.asastatsPins` surface.
 */
function mount() {
  document.body.innerHTML = "";
  mountSection("asasec", ASSETS, false);
  mountSection("nftsec", COLLECTIONS, true);
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/pins.js")];
  require("../static/js/pins.js");
  return window.asastatsPins;
}

/**
 * Return the ids of the pinnable entries in `container`, in document order.
 *
 * Only direct children are read: an NFT item is itself a `.fitem` nested
 * inside its collection, and pulling those in would make every assertion here
 * about the wrong list.
 *
 * @param {Element} container - the element holding the entries.
 * @returns {string[]} entry ids in document order.
 */
function orderOf(container) {
  return Array.from(container.children)
    .filter((el) => el.classList.contains("fitem"))
    .map((el) => el.id);
}

/** The container holding the asset entries. */
function assetContainer() {
  return document.getElementById(ASSET).parentNode;
}

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(document, "readyState", {
    value: "complete",
    configurable: true,
  });
  window.history.pushState({}, "", "/VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU");
});

describe("storage key", () => {
  test("is scoped to the address being read", () => {
    const pins = mount();

    expect(pins.storageKey()).toBe(
      "pins:VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU",
    );
  });

  test("separates two addresses", () => {
    const pins = mount();
    const first = pins.storageKey();
    window.history.pushState({}, "", "/540A5D8CEC896E073F9170AF0A962503E69147CF");

    expect(pins.storageKey()).not.toBe(first);
  });
});

describe("pinning", () => {
  test("moves the entry to the top of its section", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);
    const last = served[served.length - 1];

    pins.toggle(last, document);

    expect(orderOf(container)[0]).toBe(last);
  });

  test("leaves everything else in the order the server sent", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);
    const last = served[served.length - 1];

    pins.toggle(last, document);

    const rest = orderOf(container).slice(1);
    expect(rest).toEqual(served.filter((id) => id !== last));
  });

  test("a second pin lands below the first, not above it", () => {
    const pins = mount();
    const container = assetContainer();

    pins.toggle(ALGO, document);
    pins.toggle(ASSET, document);

    expect(orderOf(container).slice(0, 2)).toEqual([ALGO, ASSET]);
  });

  test("unpinning puts the entry back where it was served", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);

    pins.toggle(served[served.length - 1], document);
    pins.toggle(served[served.length - 1], document);

    expect(orderOf(container)).toEqual(served);
  });

  test("unpinning the first of two leaves the second pinned", () => {
    const pins = mount();
    const container = assetContainer();

    pins.toggle(ALGO, document);
    pins.toggle(ASSET, document);
    pins.toggle(ALGO, document);

    expect(orderOf(container)[0]).toBe(ASSET);
  });

  test("a collection pins within its own section", () => {
    const pins = mount();
    const collection = document.getElementById(COLLECTION);
    const container = collection.parentNode;

    pins.toggle(COLLECTION, document);

    expect(orderOf(container)[0]).toBe(COLLECTION);
    // The asset section is a different container and must not have moved.
    expect(orderOf(assetContainer())[0]).not.toBe(COLLECTION);
  });
});

describe("state on the controls", () => {
  test("a pinned entry presses its control and marks its row", () => {
    const pins = mount();

    pins.toggle(ASSET, document);

    const button = document.querySelector(`[data-pin="${ASSET}"]`);
    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(document.getElementById(ASSET).classList.contains("pinned")).toBe(true);
  });

  test("every control ships unpressed", () => {
    mount();

    const pressed = Array.from(document.querySelectorAll("[data-pin]")).filter(
      (b) => b.getAttribute("aria-pressed") === "true",
    );
    expect(pressed).toHaveLength(0);
  });

  test("unpinning releases the control and the row", () => {
    const pins = mount();

    pins.toggle(ASSET, document);
    pins.toggle(ASSET, document);

    const button = document.querySelector(`[data-pin="${ASSET}"]`);
    expect(button.getAttribute("aria-pressed")).toBe("false");
    expect(document.getElementById(ASSET).classList.contains("pinned")).toBe(false);
  });
});

describe("persistence", () => {
  test("a pin survives a reload", () => {
    const pins = mount();
    pins.toggle(ASSET, document);

    const reloaded = mount();

    expect(orderOf(assetContainer())[0]).toBe(ASSET);
    expect(reloaded.read()).toEqual([ASSET]);
  });

  test("pins are restored in the order they were made", () => {
    const pins = mount();
    pins.toggle(ALGO, document);
    pins.toggle(ASSET, document);

    mount();

    expect(orderOf(assetContainer()).slice(0, 2)).toEqual([ALGO, ASSET]);
  });

  test("another address's pins do not apply", () => {
    const pins = mount();
    pins.toggle(ASSET, document);
    window.history.pushState({}, "", "/540A5D8CEC896E073F9170AF0A962503E69147CF");

    mount();

    expect(document.getElementById(ASSET).classList.contains("pinned")).toBe(false);
  });

  test("an id no longer on the page is ignored rather than throwing", () => {
    const pins = mount();
    pins.write(["fgone-since-yesterday", ASSET]);

    mount();

    expect(orderOf(assetContainer())[0]).toBe(ASSET);
  });
});

describe("unreadable storage", () => {
  test("malformed JSON reads as no pins", () => {
    const pins = mount();
    localStorage.setItem(pins.storageKey(), "{not json");

    expect(pins.read()).toEqual([]);
  });

  test("a stored non-array reads as no pins", () => {
    const pins = mount();
    localStorage.setItem(pins.storageKey(), '{"f1": true}');

    expect(pins.read()).toEqual([]);
  });

  test("non-string entries are dropped", () => {
    const pins = mount();
    localStorage.setItem(pins.storageKey(), '["' + ASSET + '", 7, null]');

    expect(pins.read()).toEqual([ASSET]);
  });

  test("the page still renders in served order", () => {
    const pins = mount();
    const served = orderOf(assetContainer());
    localStorage.setItem(pins.storageKey(), "{not json");

    mount();

    expect(orderOf(assetContainer())).toEqual(served);
  });
});

describe("storage that throws", () => {
  /**
   * Swap localStorage for one whose `method` throws; returns a restore function.
   *
   * Lifted from layout.test.js, and see its comment for why it is done this
   * way: spying on `Storage.prototype` misses `jest-localstorage-mock`, and
   * assigning the method misses real jsdom's Proxy-backed Storage. Redefining
   * the property on `window` is above both.
   *
   * @param {string} method - the method to break.
   * @returns {Function} restores the real localStorage.
   */
  function breakStorage(method) {
    const real = window.localStorage;
    const broken = {
      getItem: (k) => real.getItem(k),
      setItem: (k, v) => real.setItem(k, v),
      removeItem: (k) => real.removeItem(k),
      clear: () => real.clear(),
    };
    broken[method] = () => {
      throw new Error("denied");
    };
    const define = (value) =>
      Object.defineProperty(window, "localStorage", { value, configurable: true });
    define(broken);
    return () => define(real);
  }

  test("an unreadable store reads as no pins", () => {
    const pins = mount();
    const restore = breakStorage("getItem");

    try {
      expect(pins.read()).toEqual([]);
    } finally {
      restore();
    }
  });

  test("an unwritable store still pins for this visit", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);
    const restore = breakStorage("setItem");

    try {
      // Private browsing: the reader gets the arrangement they asked for and
      // does not get it back tomorrow. It must not throw at them either way.
      expect(() => pins.toggle(served[served.length - 1], document)).not.toThrow();
    } finally {
      restore();
    }
  });
});

describe("clicking the control", () => {
  test("pins without opening the entry it sits in", () => {
    mount();
    const entry = document.getElementById(ASSET);
    const button = entry.querySelector("[data-pin]");
    const event = new window.MouseEvent("click", {
      bubbles: true,
      cancelable: true,
    });

    button.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
    expect(button.getAttribute("aria-pressed")).toBe("true");
  });

  test("a click elsewhere on the row is left alone", () => {
    mount();
    const summary = document.getElementById(ASSET).querySelector("summary");
    const event = new window.MouseEvent("click", {
      bubbles: true,
      cancelable: true,
    });

    summary.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
  });
});

describe("reordering with the keyboard", () => {
  /**
   * Press `key` on an entry's grip.
   *
   * A real KeyboardEvent through the delegated document listener, rather than
   * calling `move` -- the binding is half of what these tests are for.
   *
   * @param {string} id - the entry id.
   * @param {string} key - the key name.
   */
  function press(id, key) {
    const grip = document.getElementById(id).querySelector("[data-drag]");
    grip.dispatchEvent(
      new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }),
    );
  }

  test("the down arrow moves an entry one place later", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[0], "ArrowDown");

    expect(orderOf(container)[1]).toBe(served[0]);
  });

  test("the up arrow moves an entry one place earlier", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[1], "ArrowUp");

    expect(orderOf(container)[0]).toBe(served[1]);
  });

  test("Home sends an entry to the top of its group", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[served.length - 1], "Home");

    expect(orderOf(container)[0]).toBe(served[served.length - 1]);
  });

  test("End sends an entry to the bottom of its group", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[0], "End");

    expect(orderOf(container).pop()).toBe(served[0]);
  });

  test("the up arrow at the top does nothing", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[0], "ArrowUp");

    expect(orderOf(container)).toEqual(served);
  });

  test("the down arrow at the bottom does nothing", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[served.length - 1], "ArrowDown");

    expect(orderOf(container)).toEqual(served);
  });

  test("an unrelated key is left alone", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    press(served[0], "a");

    expect(orderOf(container)).toEqual(served);
  });

  test("the grip says where the entry landed", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    press(served[0], "ArrowDown");

    expect(grip.getAttribute("aria-label")).toMatch(/Now 2 of \d+\./);
  });

  test("repeated moves do not stack announcements", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    press(served[0], "ArrowDown");
    press(served[0], "ArrowDown");

    expect(grip.getAttribute("aria-label").match(/Now /g)).toHaveLength(1);
  });
});

describe("reordering is remembered", () => {
  test("a move survives a reload", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");
    grip.dispatchEvent(
      new window.KeyboardEvent("keydown", { key: "End", bubbles: true, cancelable: true }),
    );
    const after = orderOf(container);

    mount();

    expect(orderOf(assetContainer())).toEqual(after);
  });

  test("the order is stored per section", () => {
    const pins = mount();
    const served = orderOf(assetContainer());

    pins.move(document.getElementById(served[0]), 1);

    expect(Object.keys(pins.readOrder())).toEqual(["asa"]);
  });

  test("a section the reader never touched keeps the served order", () => {
    const pins = mount();
    const collection = document.getElementById(COLLECTION);
    const nftServed = orderOf(collection.parentNode);

    pins.move(document.getElementById(orderOf(assetContainer())[0]), 1);
    mount();

    expect(orderOf(document.getElementById(COLLECTION).parentNode)).toEqual(nftServed);
  });

  test("an entry that has appeared since keeps its served neighbours", () => {
    const pins = mount();
    const served = orderOf(assetContainer());
    // The reader's stored order predates the newest entry entirely.
    pins.writeOrder({ asa: served.slice(0, 1) });

    mount();

    expect(orderOf(assetContainer())).toEqual(served);
  });

  test("a malformed order reads as none", () => {
    const pins = mount();
    localStorage.setItem(pins.orderKey(), "[1,2,3]");

    expect(pins.readOrder()).toEqual({});
  });
});

describe("pinned and unpinned are separate groups", () => {
  test("a pinned entry cannot be moved below an unpinned one", () => {
    const pins = mount();
    const container = assetContainer();
    pins.toggle(ALGO, document);

    // ALGO is now the only pinned entry, so it is a group of one.
    pins.move(document.getElementById(ALGO), 5);

    expect(orderOf(container)[0]).toBe(ALGO);
  });

  test("an unpinned entry cannot be moved above a pinned one", () => {
    const pins = mount();
    const container = assetContainer();
    pins.toggle(ALGO, document);
    const firstUnpinned = orderOf(container)[1];

    pins.moveToEnd(document.getElementById(firstUnpinned), true);

    expect(orderOf(container)[0]).toBe(ALGO);
    expect(orderOf(container)[1]).toBe(firstUnpinned);
  });

  test("reordering within the pinned group works", () => {
    const pins = mount();
    const container = assetContainer();
    pins.toggle(ALGO, document);
    pins.toggle(ASSET, document);

    pins.move(document.getElementById(ASSET), -1);

    expect(orderOf(container).slice(0, 2)).toEqual([ASSET, ALGO]);
  });
});

describe("dragging with a pointer", () => {
  /**
   * Dispatch a pointer event carrying a vertical position.
   *
   * jsdom has no PointerEvent, so this is a plain Event with the two
   * properties the handlers read. That is enough: the handlers are written
   * against `clientY` and `button`, not against anything only a real pointer
   * provides.
   *
   * @param {Element} target - the element to dispatch on.
   * @param {string} type - the event name.
   * @param {number} clientY - the vertical position.
   */
  function pointer(target, type, clientY, button = 0, pointerId = 1) {
    const event = new window.Event(type, { bubbles: true, cancelable: true });
    Object.defineProperty(event, "clientY", { value: clientY });
    Object.defineProperty(event, "button", { value: button !== undefined ? button : 0 });
    Object.defineProperty(event, "pointerId", { value: pointerId !== undefined ? pointerId : 1 });
    target.dispatchEvent(event);
  }

  /**
   * Give every entry in a container a distinct, stable box.
   *
   * jsdom lays nothing out, so every `getBoundingClientRect` is zeroes and the
   * handler can never tell which neighbour the pointer has passed.
   *
   * @param {Element} container - the container whose entries to place.
   * @param {number} height - the height to give each row.
   */
  function stack(container, height) {
    orderOf(container).forEach((id, index) => {
      const el = document.getElementById(id);
      el.getBoundingClientRect = () => ({
        top: index * height,
        bottom: (index + 1) * height,
        height,
      });
    });
  }

  test("a press that never moves does not reorder", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50);
    pointer(document, "pointermove", 51);
    pointer(document, "pointerup", 51);

    expect(orderOf(container)).toEqual(served);
  });

  test("dragging past the row below swaps them", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50);
    pointer(document, "pointermove", 160);
    pointer(document, "pointerup", 160);

    expect(orderOf(container)[1]).toBe(served[0]);
  });

  test("the dragged row is marked while it moves and released after", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const entry = document.getElementById(served[0]);
    const grip = entry.querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50);
    pointer(document, "pointermove", 160);
    expect(entry.classList.contains("dragging")).toBe(true);

    pointer(document, "pointerup", 160);
    expect(entry.classList.contains("dragging")).toBe(false);
  });

  test("a drag is remembered", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50);
    pointer(document, "pointermove", 160);
    pointer(document, "pointerup", 160);

    expect(pins.readOrder().asa[1]).toBe(served[0]);
  });

  test("a cancelled drag keeps what it had already moved", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50);
    pointer(document, "pointermove", 160);
    pointer(document, "pointercancel", 160);

    expect(orderOf(container)[1]).toBe(served[0]);
  });

  test("a move with no drag in progress is ignored", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);

    expect(() => pointer(document, "pointermove", 400)).not.toThrow();
    expect(orderOf(container)).toEqual(served);
  });

  test("the grip does not open the entry it sits in", () => {
    mount();
    const grip = document.getElementById(ASSET).querySelector("[data-drag]");
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });

    grip.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
  });
});

describe("running twice", () => {
  test("a second execution does not double-bind the handlers", () => {
    // The script is a plain <script> today, but this page already pulls one in
    // through an htmx partial. A second execution used to add a second set of
    // delegated listeners, so one arrow key moved a row two places -- which
    // passes every single-test run and fails only in a suite.
    mount();
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    grip.dispatchEvent(
      new window.KeyboardEvent("keydown", {
        key: "ArrowDown",
        bubbles: true,
        cancelable: true,
      }),
    );

    expect(orderOf(container)[1]).toBe(served[0]);
  });

  test("a second execution still arranges entries that arrived since", () => {
    const pins = mount();
    pins.toggle(ASSET, document);

    // A fresh DOM, as an htmx swap would leave, then the script runs again.
    mount();

    expect(orderOf(assetContainer())[0]).toBe(ASSET);
  });
});

describe("nested entries", () => {
  test("an NFT item inside a collection is never reordered", () => {
    const pins = mount();
    const collection = document.getElementById(COLLECTION);
    const items = Array.from(collection.querySelectorAll(".fitem")).map((el) => el.id);

    pins.toggle(COLLECTION, document);

    const after = Array.from(
      document.getElementById(COLLECTION).querySelectorAll(".fitem"),
    ).map((el) => el.id);
    expect(after).toEqual(items);
  });

  test("only entries with a control are candidates", () => {
    mount();
    const withControl = document.querySelectorAll("[data-pin]").length;
    const allEntries = document.querySelectorAll(".fitem").length;

    expect(withControl).toBeLessThan(allEntries);
  });

  test("an entry without a parent or a control without an entry is ignored", () => {
    document.body.innerHTML = `
      <div class="asasec">
        <div>
          <button data-pin="orphan">Pin</button>
        </div>
      </div>`;
    jest.resetModules();
    delete require.cache[require.resolve("../static/js/pins.js")];
    expect(() => require("../static/js/pins.js")).not.toThrow();
  });
});

describe("initialization and lifecycle", () => {
  test("waits for DOMContentLoaded if document is still loading", () => {
    document.documentElement.removeAttribute("data-pins-bound");
    document.body.innerHTML = "";
    mountSection("asasec", ASSETS, false);
    Object.defineProperty(document, "readyState", {
      value: "loading",
      configurable: true,
    });
    jest.resetModules();
    delete require.cache[require.resolve("../static/js/pins.js")];

    require("../static/js/pins.js");
    expect(document.documentElement.hasAttribute("data-pins-bound")).toBe(false);

    Object.defineProperty(document, "readyState", {
      value: "complete",
      configurable: true,
    });
    document.dispatchEvent(new window.Event("DOMContentLoaded"));

    expect(document.documentElement.hasAttribute("data-pins-bound")).toBe(true);
  });

  test("does nothing if there are no data-pin controls on the page", () => {
    document.documentElement.removeAttribute("data-pins-bound");
    document.body.innerHTML = "<div>No controls here</div>";
    jest.resetModules();
    delete require.cache[require.resolve("../static/js/pins.js")];

    require("../static/js/pins.js");

    expect(document.documentElement.hasAttribute("data-pins-bound")).toBe(false);
  });
});

describe("sectionKey and container handling", () => {
  test("returns empty string and skips remembering when parent is not in a known section", () => {
    document.body.innerHTML = `
      <div id="unsectioned">
        <div class="fitem" id="orphan1">
          <button data-pin="orphan1">Pin</button>
          <button data-drag="orphan1">Drag</button>
        </div>
        <div class="fitem" id="orphan2">
          <button data-pin="orphan2">Pin</button>
          <button data-drag="orphan2">Drag</button>
        </div>
      </div>`;
    jest.resetModules();
    delete require.cache[require.resolve("../static/js/pins.js")];
    require("../static/js/pins.js");

    const pins = window.asastatsPins;
    const entry = document.getElementById("orphan1");
    expect(pins.move(entry, 1)).toBe(true);
    expect(pins.readOrder()).toEqual({});
  });

  test("skips layout if parent has no served entries property", () => {
    const pins = mount();
    const parent = assetContainer();
    Object.defineProperty(parent, "_asastatsServedEntries", {
      get: () => undefined,
      set: () => {},
      configurable: true,
    });
    expect(() => pins.apply(document)).not.toThrow();
  });

  test("sort comparator handles when an entry is ranked before unranked ones", () => {
    const pins = mount();
    const container = assetContainer();
    const served = orderOf(container);
    // Rank only the second item (served[1]); served[0] and served[2] are unranked
    pins.writeOrder({ asa: [served[1]] });

    mount();

    // served[1] gets rank 0, served[0] and served[2] get rank undefined
    expect(orderOf(assetContainer())[0]).toBe(served[1]);
  });
});

describe("keyboard and click edge cases", () => {
  test("preserves existing data-label when announcing position", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");
    grip.setAttribute("data-label", "Reorder handle");

    grip.dispatchEvent(
      new window.KeyboardEvent("keydown", {
        key: "ArrowDown",
        bubbles: true,
        cancelable: true,
      }),
    );

    expect(grip.getAttribute("aria-label")).toMatch(/^Reorder handle Now/);
  });

  test("ignores keydown on grip not inside a fitem", () => {
    mount();
    const strayGrip = document.createElement("button");
    strayGrip.setAttribute("data-drag", "");
    document.body.appendChild(strayGrip);

    const event = new window.KeyboardEvent("keydown", {
      key: "ArrowDown",
      bubbles: true,
      cancelable: true,
    });
    strayGrip.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
  });

  test("ignores keydown and click events without closest method", () => {
    mount();
    const event = new window.Event("keydown", { bubbles: true, cancelable: true });
    expect(() => document.dispatchEvent(event)).not.toThrow();

    const clickEvent = new window.Event("click", { bubbles: true, cancelable: true });
    expect(() => document.dispatchEvent(clickEvent)).not.toThrow();
  });
});

describe("pointer dragging edge cases", () => {
  function pointer(target, type, clientY, button = 0, pointerId = 1) {
    const event = new window.Event(type, { bubbles: true, cancelable: true });
    Object.defineProperty(event, "clientY", { value: clientY });
    Object.defineProperty(event, "button", { value: button });
    Object.defineProperty(event, "pointerId", { value: pointerId });
    target.dispatchEvent(event);
  }

  function stack(container, height) {
    orderOf(container).forEach((id, index) => {
      const el = document.getElementById(id);
      el.getBoundingClientRect = () => ({
        top: index * height,
        bottom: (index + 1) * height,
        height,
      });
    });
  }

  test("dragging upward past the row above swaps them", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[1]).querySelector("[data-drag]");

    // start at row 1 (clientY: 150), drag up to row 0 (clientY: 40)
    pointer(grip, "pointerdown", 150);
    pointer(document, "pointermove", 40);
    pointer(document, "pointerup", 40);

    expect(orderOf(container)[0]).toBe(served[1]);
    expect(orderOf(container)[1]).toBe(served[0]);
  });

  test("dragging within row bounds does not reorder", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[1]).querySelector("[data-drag]");

    // start at row 1 (top 100, bottom 200), move slightly to 120 (active drag, but within row bounds)
    pointer(grip, "pointerdown", 150);
    pointer(document, "pointermove", 120);
    // move again while already active
    pointer(document, "pointermove", 125);
    pointer(document, "pointerup", 125);

    expect(orderOf(container)).toEqual(served);
  });

  test("captures pointer when setPointerCapture is supported and releases on pointerup", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    grip.setPointerCapture = jest.fn();
    grip.hasPointerCapture = jest.fn(() => true);
    grip.releasePointerCapture = jest.fn();

    pointer(grip, "pointerdown", 50, 0, 42);
    expect(grip.setPointerCapture).toHaveBeenCalledWith(42);

    pointer(document, "pointermove", 160, 0, 42);
    pointer(document, "pointerup", 160, 0, 42);

    expect(grip.releasePointerCapture).toHaveBeenCalledWith(42);
  });

  test("survives setPointerCapture or releasePointerCapture throwing an error", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    stack(container, 100);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    grip.setPointerCapture = jest.fn(() => {
      throw new Error("capture failed");
    });
    grip.hasPointerCapture = jest.fn(() => true);
    grip.releasePointerCapture = jest.fn(() => {
      throw new Error("release failed");
    });

    expect(() => {
      pointer(grip, "pointerdown", 50, 0, 42);
      pointer(document, "pointermove", 160, 0, 42);
      pointer(document, "pointerup", 160, 0, 42);
    }).not.toThrow();
  });

  test("ignores pointerdown with non-primary button", () => {
    mount();
    const container = assetContainer();
    const served = orderOf(container);
    const grip = document.getElementById(served[0]).querySelector("[data-drag]");

    pointer(grip, "pointerdown", 50, 2); // right click

    pointer(document, "pointermove", 160);
    expect(document.getElementById(served[0]).classList.contains("dragging")).toBe(
      false
    );
  });

  test("ignores pointerdown on a grip not inside a fitem", () => {
    mount();
    const strayGrip = document.createElement("button");
    strayGrip.setAttribute("data-drag", "");
    document.body.appendChild(strayGrip);

    expect(() => pointer(strayGrip, "pointerdown", 50)).not.toThrow();
    expect(() => pointer(document, "pointerdown", 50)).not.toThrow();
  });

  test("ignores pointerup when no drag was started", () => {
    mount();
    expect(() => pointer(document, "pointerup", 50)).not.toThrow();
  });
});
