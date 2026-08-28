/**
 * @jest-environment jsdom
 */

/**
 * Build one section with `total` rows, folded past `shown`.
 *
 * Synthetic rather than the captured page: the fixture is a three-asset trim,
 * so nothing in it is ever folded and there would be nothing to unfold. The
 * behaviour under test does not depend on what a row contains.
 *
 * @param {object} options - section shape.
 * @param {string} options.section - "asasec" or "nftsec".
 * @param {number} options.total - how many rows to render.
 * @param {number} options.shown - the batch size, and the first fold.
 * @param {boolean} options.control - whether to render the show-more button.
 * @param {boolean} options.initial - whether to publish `data-initial`.
 * @returns {Element} the section element.
 */
function mountSection({
  section = "asasec",
  total = 10,
  shown = 4,
  control = true,
  initial = true,
  noun = "assets",
} = {}) {
  const wrap = document.createElement("div");
  wrap.className = `${section} section-list`;
  if (initial) wrap.setAttribute("data-initial", String(shown));

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
      '<button type="button" class="show-more" data-show-more ' +
      `data-noun="${noun}" aria-expanded="false">` +
      `<span class="show-more-open">Show ${Math.min(total - shown, shown)} more ${noun}</span>` +
      `<span class="show-more-close">Show fewer ${noun}</span></button>`;
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

/** How many rows of `section` are currently showing. */
function showing(section) {
  return section.querySelectorAll(".fitem:not(.folded)").length;
}

/** The text of the "show more" half of the label. */
function label(section) {
  return section.querySelector(".show-more-open").textContent;
}

beforeEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-showmore-bound");
  Object.defineProperty(document, "readyState", {
    value: "complete",
    configurable: true,
  });
});

describe("unfolding a batch at a time", () => {
  test("a press reveals one batch, not the whole tail", () => {
    // The rule this replaced revealed everything in one press, which made the
    // control's own label untrue: "Show 39 more assets" over a button that was
    // an unfold rather than a load-more.
    const section = mountSection({ total: 30, shown: 4 });
    load();

    press(section);

    expect(showing(section)).toBe(8);
  });

  test("each further press adds another batch", () => {
    const section = mountSection({ total: 30, shown: 4 });
    load();

    press(section);
    press(section);
    press(section);

    expect(showing(section)).toBe(16);
  });

  test("the last press reveals only what is left", () => {
    const section = mountSection({ total: 10, shown: 4 });
    load();

    press(section);
    press(section);

    expect(showing(section)).toBe(10);
  });

  test("a press past the end collapses back to the first batch", () => {
    // Once everything is showing the only thing left to offer is putting it
    // back, which is what the second label says.
    const section = mountSection({ total: 10, shown: 4 });
    load();

    press(section);
    press(section);
    press(section);

    expect(showing(section)).toBe(4);
  });

  test("the label names what the next press actually does", () => {
    const section = mountSection({ total: 30, shown: 4 });
    load();

    press(section);
    expect(label(section)).toBe("Show 4 more assets");
  });

  test("the label counts down on the last batch", () => {
    const section = mountSection({ total: 10, shown: 4 });
    load();

    press(section);
    expect(label(section)).toBe("Show 2 more assets");
  });

  test("the noun comes from the control, not from the script", () => {
    // Hardcoding it would mean two copies of the plural in two files, which is
    // how "1 more collections" gets shipped.
    const section = mountSection({
      section: "nftsec",
      total: 30,
      shown: 4,
      noun: "collections",
    });
    load();

    press(section);
    expect(label(section)).toBe("Show 4 more collections");
  });

  test("the control reports its state", () => {
    const section = mountSection({ total: 10, shown: 4 });
    load();
    const button = section.querySelector("[data-show-more]");

    press(section);
    expect(button.getAttribute("aria-expanded")).toBe("false");

    press(section);
    expect(button.getAttribute("aria-expanded")).toBe("true");

    press(section);
    expect(button.getAttribute("aria-expanded")).toBe("false");
  });

  test("a section that publishes no batch size still unfolds", () => {
    // Degrades to the old behaviour rather than to one row per press: a
    // template that forgets `data-initial` should be tidy, not unusable.
    const section = mountSection({ total: 10, shown: 4, initial: false });
    load();

    press(section);

    expect(showing(section)).toBe(10);
  });

  test("only the rows are counted", () => {
    // A container may hold something that is not a row -- a note, a heading
    // arriving later -- and counting those would shift the fold by however
    // many of them there are.
    const section = mountSection({ total: 10, shown: 4 });
    const note = document.createElement("p");
    const container = section.querySelector("[data-folding]");
    container.insertBefore(note, container.firstChild);
    load();

    press(section);

    expect(showing(section)).toBe(8);
  });
});

describe("two sections", () => {
  test("unfolding one leaves the other alone", () => {
    const assets = mountSection({ section: "asasec", total: 30, shown: 4 });
    const collections = mountSection({ section: "nftsec", total: 30, shown: 4 });
    load();

    press(assets);

    expect(showing(assets)).toBe(8);
    expect(showing(collections)).toBe(4);
  });

  test("each section counts its own batches", () => {
    // The count lives on the container rather than in one module-level
    // variable, so two sections cannot share a position in the sequence.
    const assets = mountSection({ section: "asasec", total: 30, shown: 4 });
    const collections = mountSection({ section: "nftsec", total: 30, shown: 10 });
    load();

    press(assets);
    press(assets);
    press(collections);

    expect(showing(assets)).toBe(12);
    expect(showing(collections)).toBe(20);
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

  test("a control that names no noun still says something", () => {
    // `data-noun` is the template's, and a template that forgets it should
    // read a little blandly rather than render "Show 4 more undefined".
    const section = mountSection({ total: 30, shown: 4 });
    section.querySelector("[data-show-more]").removeAttribute("data-noun");
    load();

    press(section);

    expect(label(section)).toBe("Show 4 more rows");
  });

  test("a control with no label is still usable", () => {
    // The rows are the point; the count is a courtesy.
    const section = mountSection({ total: 30, shown: 4 });
    section.querySelector(".show-more-open").remove();
    load();

    press(section);

    expect(showing(section)).toBe(8);
  });
});

describe("wiring", () => {
  test("a click elsewhere does nothing", () => {
    const section = mountSection({ total: 30, shown: 4 });
    load();

    document.body.dispatchEvent(
      new window.MouseEvent("click", { bubbles: true, cancelable: true }),
    );

    expect(showing(section)).toBe(4);
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
    // partial, and a second set of delegated handlers would count two batches
    // per press.
    const section = mountSection({ total: 30, shown: 4 });
    load();
    load();

    press(section);

    expect(showing(section)).toBe(8);
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
    const section = mountSection({ total: 30, shown: 4 });
    load();
    const button = section.querySelector("[data-show-more]");
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    event.preventDefault();

    button.dispatchEvent(event);

    expect(showing(section)).toBe(4);
  });
});


describe("on the dynamic designs", () => {
  test("it stands down entirely", () => {
    // Those designs fold from the toolbar, which also filters and sorts. Two
    // handlers on one control would both act -- a batch revealed *and* the
    // batch counted -- so the second press would have nothing left to do.
    const page = document.createElement("div");
    page.className = "dynamic-page";
    document.body.appendChild(page);
    mountSection();

    load();

    // Asserted on the binding rather than on a press: this file's earlier
    // tests have already left delegated handlers on `document`, and those keep
    // acting whatever a later execution decides. The attribute is what a fresh
    // page would see.
    expect(document.documentElement.hasAttribute("data-showmore-bound")).toBe(false);
    page.remove();
  });
});
