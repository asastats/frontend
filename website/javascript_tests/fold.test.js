/**
 * The reader's own fold size, across the three files that honour it.
 *
 * One suite rather than three additions, because the property that matters is
 * that they *agree*: `base.html` stamps the attribute, the stylesheet acts on
 * it before paint, and `toolbar.js` (dynamic designs) and `showmore.js`
 * (design 1) act on it afterwards. A test per file would pin three behaviours
 * and miss the one thing that breaks -- two of them reading different numbers.
 */

/**
 * @jest-environment jsdom
 */

"use strict";

const T = require("../static/js/theme.js");

/**
 * Load a script against the current DOM, the way its own suite does.
 *
 * **`require`, not `new Function` over the file's text.** The first version of
 * this helper read the source and eval'd it, which runs the code but is
 * invisible to istanbul - the tests passed while the coverage report showed the
 * lines they exercise as untouched. A test that cannot be seen to have run is
 * indistinguishable from one that does nothing.
 */
function run(file) {
  const id = "../static/js/" + file;
  jest.resetModules();
  delete require.cache[require.resolve(id)];
  require(id);
}

/** A section with `count` rows, folded at `initial` the way the server does. */
function section(kind, count, initial) {
  const cls = kind === "nft" ? "nftsec" : "asasec";
  const rows = [];
  for (let i = 0; i < count; i += 1) {
    rows.push(
      `<details id="f${i}" class="fitem${i >= initial ? " folded" : ""}"></details>`
    );
  }
  return `
    <div class="${cls} section-list" data-initial="${initial}">
      <div data-folding>${rows.join("")}</div>
      <div class="mt-3">
        <button type="button" class="show-more" data-show-more
                data-noun="${kind === "nft" ? "collections" : "assets"}"
                aria-expanded="false">
          <span class="show-more-open">Show ${initial} more</span>
          <span class="show-more-close">Show fewer</span>
        </button>
      </div>
    </div>`;
}

describe("the fold size a reader chose", () => {
  afterEach(() => {
    document.documentElement.removeAttribute("data-fold-assets");
    document.documentElement.removeAttribute("data-fold-collections");
    document.documentElement.classList.remove("prefold");
    document.documentElement.removeAttribute("data-showmore-bound");
    localStorage.clear();
    document.body.innerHTML = "";
  });

  describe("showmore.js, which design 1 uses", () => {
    function press() {
      document.querySelector("[data-show-more]").dispatchEvent(
        new window.MouseEvent("click", { bubbles: true, cancelable: true })
      );
    }

    function visible() {
      return document.querySelectorAll(".fitem:not(.folded)").length;
    }

    it("reveals the reader's batch rather than the server's", () => {
      document.body.innerHTML = section("asa", 200, 20);
      document.documentElement.setAttribute("data-fold-assets", "50");
      run("showmore.js");

      press();

      // One press is one batch, and the batch is now the reader's 50.
      expect(visible()).toBe(100);
    });

    it("falls back to the server's number when nothing is chosen", () => {
      document.body.innerHTML = section("asa", 200, 20);
      run("showmore.js");

      press();

      expect(visible()).toBe(40);
    });

    it("shows everything at once for `all`", () => {
      document.body.innerHTML = section("asa", 200, 20);
      document.documentElement.setAttribute("data-fold-assets", "all");
      run("showmore.js");

      press();

      expect(visible()).toBe(200);
    });

    it("hides the control for `all`, which has nothing left to offer", () => {
      document.body.innerHTML = section("asa", 200, 20);
      document.documentElement.setAttribute("data-fold-assets", "all");
      run("showmore.js");

      press();

      expect(document.querySelector(".show-more").parentNode.hidden).toBe(true);
    });

    it("reads the collections attribute for an NFT section", () => {
      document.body.innerHTML = section("nft", 100, 10);
      document.documentElement.setAttribute("data-fold-assets", "all");
      document.documentElement.setAttribute("data-fold-collections", "50");
      run("showmore.js");

      press();

      // `all` belongs to the other section and must not leak into this one.
      expect(visible()).toBe(100);
    });

    it("drops `prefold` once it owns the fold", () => {
      document.body.innerHTML = section("asa", 200, 20);
      document.documentElement.classList.add("prefold");
      run("showmore.js");

      press();

      expect(document.documentElement.classList.contains("prefold")).toBe(false);
    });

    it("survives a control that is no longer in the document", () => {
      // **Defensive, and reachable.** `paint` is exported and the address page
      // re-renders sections from htmx partials, so a control can be detached
      // between the render that found it and the paint that writes to it.
      // Without the guard that is a TypeError on `parentNode.hidden`.
      document.body.innerHTML = section("asa", 50, 20);
      run("showmore.js");
      const container = document.querySelector("[data-folding]");
      const button = document.querySelector("[data-show-more]");
      button.remove();

      expect(() =>
        window.asastatsShowMore.paint(container, button)
      ).not.toThrow();
    });

    it("leaves `prefold` alone until something is pressed", () => {
      document.body.innerHTML = section("asa", 200, 20);
      document.documentElement.classList.add("prefold");
      run("showmore.js");

      // **Nothing paints this page on load.** Until a press, the stylesheet is
      // the reader's fold, so dropping the class at bind time would revert
      // their choice the moment the script loaded.
      expect(document.documentElement.classList.contains("prefold")).toBe(true);
    });
  });

  describe("theme.js, which stores the choice", () => {
    it("writes the key the head script reads and stamps the document", () => {
      document.body.innerHTML = `
        <div data-fold-target="assets">
          <input type="radio" name="fold-assets" value="50">
          <input type="radio" name="fold-assets" value="all">
        </div>`;
      T.wireFoldPicker(document);

      const radio = document.querySelector("input[value='50']");
      radio.checked = true;
      radio.dispatchEvent(new window.Event("change", { bubbles: true }));

      expect(localStorage.getItem("fold-assets")).toBe("50");
      expect(document.documentElement.getAttribute("data-fold-assets")).toBe("50");
    });

    it("restores the saved choice onto the radios", () => {
      localStorage.setItem("fold-collections", "all");
      document.body.innerHTML = `
        <div data-fold-target="collections">
          <input type="radio" name="fold-collections" value="10">
          <input type="radio" name="fold-collections" value="all">
        </div>`;
      T.wireFoldPicker(document);

      expect(document.querySelector("input[value='all']").checked).toBe(true);
    });

    it("survives storage refusing the write", () => {
      // Replaced whole, for the reason the read test gives: a prototype spy
      // does not reach jsdom's `localStorage`, and the assertions below hold
      // either way, so the test would look green over an unrun catch.
      const real = window.localStorage;
      Object.defineProperty(window, "localStorage", {
        configurable: true,
        value: {
          getItem: () => null,
          setItem() {
            throw new Error("QuotaExceededError");
          },
        },
      });

      // Private browsing refuses the write; the choice must still apply to the
      // page in front of the reader.
      expect(T.applyFold("fold-assets", "50")).toBe(true);
      expect(document.documentElement.getAttribute("data-fold-assets")).toBe("50");

      Object.defineProperty(window, "localStorage", {
        configurable: true,
        value: real,
      });
    });

    it("wires the radios when storage refuses to be read", () => {
      // **The read can throw as well as the write.** Private browsing and
      // blocked site-data both refuse `getItem`, and a picker that threw there
      // would take the whole appearance page down rather than lose a
      // preference - the choices must still be selectable, just not restored.
      // **The whole object is replaced, not a prototype method.** jsdom's
      // `localStorage` does not dispatch through `Storage.prototype`, so
      // spying there leaves the real read in place - and the test then passes
      // whether or not the catch ever runs, which is worse than no test.
      const real = window.localStorage;
      Object.defineProperty(window, "localStorage", {
        configurable: true,
        value: {
          getItem() {
            throw new Error("SecurityError");
          },
          setItem() {},
        },
      });
      document.body.innerHTML = `
        <div data-fold-target="assets">
          <input type="radio" name="fold-assets" value="50" checked>
        </div>`;

      // Pre-checked above, so this can only pass if the read threw: a working
      // read returns nothing for this key and leaves the radio exactly as it
      // is, which would not distinguish the two paths at all.
      expect(() => T.wireFoldPicker(document)).not.toThrow();

      Object.defineProperty(window, "localStorage", {
        configurable: true,
        value: real,
      });
    });

    it("defaults to the whole document when given no root", () => {
      document.body.innerHTML = `
        <div data-fold-target="assets">
          <input type="radio" name="fold-assets" value="50">
        </div>`;

      expect(T.wireFoldPicker()).toBe(1);
    });

    it("binds each radio once, however often it is asked", () => {
      // **The failure this guards is silent.** Two handlers on one control both
      // act, and in this codebase that has already shipped once as a button
      // that simply looked dead. The page wires on load and again after an
      // htmx swap, so a second call is the normal case, not an edge one.
      document.body.innerHTML = `
        <div data-fold-target="assets">
          <input type="radio" name="fold-assets" value="50">
        </div>`;

      expect(T.wireFoldPicker(document)).toBe(1);
      expect(T.wireFoldPicker(document)).toBe(0);
    });

    it("ignores an empty value rather than stamping nothing", () => {
      expect(T.applyFold("fold-assets", "")).toBe(false);
    });
  });
});
