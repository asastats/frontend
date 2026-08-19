/**
 * @jest-environment jsdom
 */

const fs = require("fs");
const path = require("path");

const capturedPage = fs.readFileSync(
  path.resolve(__dirname, "./address.html"),
  "utf8",
);

/** Entry ids the captured page offers a pin control for. */
const ASSET = "f393401013";
const ALGO = "f0";
const COLLECTION = "fknith3ds";

/**
 * Mount the captured address page and load pins.js against it.
 *
 * The module is an IIFE that arranges the page as it loads, so it has to be
 * required *after* the DOM exists and re-required for every test -- hence the
 * cache eviction rather than a plain require at the top of the file.
 *
 * @returns {object} the `window.asastatsPins` surface.
 */
function mount() {
  document.body.innerHTML = capturedPage;
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
});
