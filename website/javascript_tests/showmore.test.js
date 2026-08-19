/**
 * @jest-environment jsdom
 */

/**
 * Build one section with `total` rows, `shown` of them unfolded.
 *
 * Synthetic rather than the captured page: the fixture is a three-asset trim,
 * so the cutoff's floor keeps every row visible and there is nothing to unfold.
 * The behaviour under test does not depend on what a row contains.
 *
 * @param {object} options - section shape.
 * @param {string} options.section - "asasec" or "nftsec".
 * @param {number} options.total - how many rows to render.
 * @param {number} options.shown - how many are not folded.
 * @param {boolean} options.control - whether to render the show-more button.
 * @returns {Element} the section element.
 */
function mountSection({ section = "asasec", total = 10, shown = 4, control = true } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `${section} section-list`;

  const rows = document.createElement("div");
  rows.setAttribute("data-folding", "");
  for (let i = 0; i < total; i += 1) {
    const row = document.createElement("details");
    row.className = i < shown ? "fitem" : "fitem folded";
    row.id = `f${i}`;
    rows.appendChild(row);
  }
  wrap.appendChild(rows);

  if (control) {
    const holder = document.createElement("div");
    holder.innerHTML =
      '<button type="button" class="show-more" data-show-more aria-expanded="false">' +
      `<span class="show-more-open">Show ${total - shown} more</span>` +
      '<span class="show-more-close">Show fewer</span></button>';
    wrap.appendChild(holder);
  }

  document.body.appendChild(wrap);
  return wrap;
}

/** Load showmore.js against the current DOM. */
function load() {
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/showmore.js")];
  require("../static/js/showmore.js");
  return window.asastatsShowMore;
}

/** Click the show-more control inside `section`. */
function press(section) {
  section
    .querySelector("[data-show-more]")
    .dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-showmore-bound");
  Object.defineProperty(document, "readyState", {
    value: "complete",
    configurable: true,
  });
});

describe("unfolding", () => {
  test("a press reveals the folded rows", () => {
    const section = mountSection();
    load();

    press(section);

    expect(
      section.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(true);
  });

  test("a second press folds them again", () => {
    const section = mountSection();
    load();

    press(section);
    press(section);

    expect(
      section.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(false);
  });

  test("the control reports its state", () => {
    const section = mountSection();
    load();
    const button = section.querySelector("[data-show-more]");

    press(section);
    expect(button.getAttribute("aria-expanded")).toBe("true");

    press(section);
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });

  test("the rows themselves are not touched", () => {
    // The stylesheet reads the container's class; rewriting sixty rows would
    // be the same result at sixty times the cost, and would fight the filter.
    const section = mountSection({ total: 10, shown: 4 });
    load();

    press(section);

    expect(section.querySelectorAll(".fitem.folded")).toHaveLength(6);
  });
});

describe("two sections", () => {
  test("unfolding one leaves the other alone", () => {
    const assets = mountSection({ section: "asasec" });
    const collections = mountSection({ section: "nftsec" });
    load();

    press(assets);

    expect(
      assets.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(true);
    expect(
      collections.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(false);
  });

  test("each control finds its own rows", () => {
    const assets = mountSection({ section: "asasec" });
    const collections = mountSection({ section: "nftsec" });
    const api = load();

    expect(api.containerFor(assets.querySelector("[data-show-more]"))).toBe(
      assets.querySelector("[data-folding]"),
    );
    expect(api.containerFor(collections.querySelector("[data-show-more]"))).toBe(
      collections.querySelector("[data-folding]"),
    );
  });
});

describe("finding the rows", () => {
  test("falls back to the section when the control is re-wrapped", () => {
    // The control sits after its container today. If markup ever puts another
    // element between them, unfolding the right section still beats nothing.
    const section = mountSection();
    const holder = section.querySelector("[data-show-more]").parentNode;
    const spacer = document.createElement("div");
    section.insertBefore(spacer, holder);
    const api = load();

    expect(api.containerFor(section.querySelector("[data-show-more]"))).toBe(
      section.querySelector("[data-folding]"),
    );
  });

  test("a control with no section at all is ignored", () => {
    document.body.innerHTML =
      '<button data-show-more aria-expanded="false"></button>';
    const api = load();
    const button = document.querySelector("[data-show-more]");

    expect(() => api.toggle(button)).not.toThrow();
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });

  test("a control with no parent is ignored", () => {
    const api = load();
    const orphan = document.createElement("button");
    orphan.setAttribute("data-show-more", "");

    expect(api.containerFor(orphan)).toBeNull();
  });
});

describe("wiring", () => {
  test("a click elsewhere does nothing", () => {
    const section = mountSection();
    load();

    document.body.dispatchEvent(
      new window.MouseEvent("click", { bubbles: true, cancelable: true }),
    );

    expect(
      section.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(false);
  });

  test("the control does not submit or navigate", () => {
    const section = mountSection();
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });

    section.querySelector("[data-show-more]").dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
  });

  test("a second execution does not toggle twice per click", () => {
    // Same hazard pins.js had: this page pulls a script in through an htmx
    // partial, and a second set of delegated handlers would toggle and
    // immediately untoggle, so the button would look dead.
    const section = mountSection();
    load();
    load();

    press(section);

    expect(
      section.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(true);
  });

  test("defers binding while the document is still parsing", () => {
    // Asserted through the marker rather than by clicking: jsdom keeps one
    // document for the whole file, so handlers bound by earlier tests are still
    // attached and "nothing happens yet" is not observable from a click.
    Object.defineProperty(document, "readyState", {
      value: "loading",
      configurable: true,
    });
    mountSection();

    load();
    expect(document.documentElement.hasAttribute("data-showmore-bound")).toBe(false);

    document.dispatchEvent(new window.Event("DOMContentLoaded"));
    expect(document.documentElement.hasAttribute("data-showmore-bound")).toBe(true);
  });

  test("ignores click when target lacks closest method", () => {
    mountSection();
    load();
    const event = new window.Event("click", { bubbles: true, cancelable: true });
    expect(() => document.dispatchEvent(event)).not.toThrow();
  });

  test("ignores an event that was already defaultPrevented by another handler", () => {
    const section = mountSection();
    load();
    const button = section.querySelector("[data-show-more]");
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    event.preventDefault();

    button.dispatchEvent(event);

    expect(
      section.querySelector("[data-folding]").classList.contains("unfolded"),
    ).toBe(false);
  });
});
