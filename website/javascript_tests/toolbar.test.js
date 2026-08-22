/**
 * @jest-environment jsdom
 *
 * The money-column toolbar: filtering, sorting, grouping, cutoff, currency.
 *
 * Synthetic DOM rather than the captured page, for the reason `pins.test.js`
 * gives: what these tests are about is the shape the toolbar acts on -- an
 * asset card carrying sort keys, a venue group carrying positions, each
 * position carrying a category and an owner -- and reading a fixture would tie
 * them to whichever design happens to render it today.
 *
 * The numbers are chosen so nothing is ambiguous: the categories total 100, no
 * two assets share a value, and the cutoff cases land on exact boundaries.
 */

const ALGO_PER_USD = 0.1;

/**
 * Build one position row.
 *
 * @param {object} spec - {owner, cat, value, search, pid}
 * @returns {Element}
 */
function position(spec) {
  const row = document.createElement("div");
  row.className = "position";
  row.setAttribute("data-owner", spec.owner);
  row.setAttribute("data-cat", spec.cat);
  row.setAttribute("data-value", String(spec.value));
  row.setAttribute("data-search", spec.search || "");
  if (spec.pid) row.setAttribute("data-pid", spec.pid);

  const cell = document.createElement("div");
  cell.className = "position-val";
  const amount = document.createElement("span");
  amount.className = "amt val";
  amount.setAttribute("data-val", String(spec.value));
  const unit = document.createElement("span");
  unit.className = "u unit";
  unit.textContent = "ALGO";
  cell.appendChild(amount);
  cell.appendChild(unit);
  row.appendChild(cell);
  return row;
}

/**
 * Build one venue group inside an asset card.
 *
 * @param {object} spec - {venue, asset, positions}
 * @returns {Element}
 */
function group(spec) {
  const wrap = document.createElement("div");
  wrap.className = "pgroup";
  wrap.setAttribute("data-positions", "");
  wrap.setAttribute("data-venue", spec.venue);
  wrap.setAttribute("data-asset", spec.asset);

  const head = document.createElement("div");
  head.className = "pgroup-head";
  const name = document.createElement("span");
  name.className = "pgroup-name";
  const venue = document.createElement("span");
  venue.className = "pgroup-venue";
  if (spec.href) {
    const link = document.createElement("a");
    link.className = "out";
    link.href = spec.href;
    link.textContent = spec.venue;
    venue.appendChild(link);
  } else {
    venue.textContent = spec.venue;
  }
  const asset = document.createElement("span");
  asset.className = "pgroup-asset";
  asset.textContent = spec.asset;
  const count = document.createElement("span");
  count.className = "n";
  count.textContent = String(spec.positions.length);
  name.appendChild(venue);
  name.appendChild(asset);
  name.appendChild(count);

  const total = document.createElement("span");
  total.className = "pgroup-total num val";
  total.setAttribute("data-val", "0");
  total.appendChild(document.createTextNode("0.00 "));
  const unit = document.createElement("span");
  unit.className = "unit";
  unit.textContent = "ALGO";
  total.appendChild(unit);

  head.appendChild(name);
  head.appendChild(total);
  wrap.appendChild(head);
  spec.positions.forEach((row) => wrap.appendChild(row));
  return wrap;
}

/**
 * Build one asset card.
 *
 * @param {object} spec - {id, unit, value, amount, positions, groups}
 * @returns {Element}
 */
function card(spec) {
  const details = document.createElement("details");
  details.className = "fitem mcard";
  details.id = spec.id;
  details.setAttribute("data-sort-value", String(spec.value));
  details.setAttribute("data-sort-amount", String(spec.amount));
  details.setAttribute("data-sort-name", spec.unit.toLowerCase());
  details.setAttribute("data-sort-positions", String(spec.positions));
  details.setAttribute("data-search", spec.search || spec.unit);

  const head = document.createElement("summary");
  head.className = "chead";
  const value = document.createElement("span");
  value.className = "cval";
  const figure = document.createElement("span");
  figure.className = "v val";
  figure.setAttribute("data-val", String(spec.value));
  const unit = document.createElement("span");
  unit.className = "u unit";
  unit.textContent = "ALGO";
  value.appendChild(figure);
  value.appendChild(unit);
  const pin = document.createElement("button");
  pin.setAttribute("data-pin", spec.id);
  head.appendChild(value);
  head.appendChild(pin);

  const body = document.createElement("div");
  body.className = "cbody";
  const inner = document.createElement("div");
  inner.className = "cbody-inner";
  const holder = document.createElement("div");
  holder.className = "program-groups";
  (spec.groups || []).forEach((one) => holder.appendChild(one));
  inner.appendChild(holder);
  body.appendChild(inner);

  details.appendChild(head);
  details.appendChild(body);
  return details;
}

/** One category figure in the band. */
function fig(key, value) {
  const button = document.createElement("button");
  button.className = `fig cat-${key}`;
  button.setAttribute("data-band", key);
  button.setAttribute("aria-pressed", "true");
  const figure = document.createElement("span");
  figure.className = "fig-val num val";
  figure.setAttribute("data-val", String(value));
  figure.appendChild(document.createTextNode("0.00 "));
  const unit = document.createElement("span");
  unit.className = "unit";
  unit.textContent = "ALGO";
  figure.appendChild(unit);
  const share = document.createElement("span");
  share.className = "fig-share num";
  button.appendChild(figure);
  button.appendChild(share);
  return button;
}

/** One segment of the allocation bar. */
function segment(key) {
  const button = document.createElement("button");
  button.className = `cat-${key}`;
  button.setAttribute("data-band", key);
  button.setAttribute("aria-pressed", "true");
  return button;
}

/** A segmented control. */
function seg(id, attribute, values, on) {
  const wrap = document.createElement("div");
  wrap.className = "seg";
  wrap.id = id;
  values.forEach((value) => {
    const button = document.createElement("button");
    button.setAttribute(attribute, value);
    button.setAttribute("aria-pressed", value === on ? "true" : "false");
    button.textContent = value;
    wrap.appendChild(button);
  });
  return wrap;
}

/**
 * Mount a whole money page.
 *
 * Four assets across three venues, four categories, values that sum to 100 so
 * every share is readable at a glance.
 */
function mountPage() {
  document.body.innerHTML = "";
  const page = document.createElement("div");
  page.className = "money-page";

  const total = document.createElement("h1");
  total.className = "total";
  const head = document.createElement("span");
  head.className = "pricetip";
  head.setAttribute("data-pricealgo", String(ALGO_PER_USD));
  head.setAttribute("data-totalwnft", "150");
  head.setAttribute("data-totalnft", "50");
  total.appendChild(head);
  page.appendChild(total);
  const sub = document.createElement("div");
  sub.className = "total-sub";
  const subNum = document.createElement("span");
  subNum.className = "num";
  sub.appendChild(subNum);
  page.appendChild(sub);
  const note = document.createElement("p");
  note.className = "total-note";
  page.appendChild(note);
  // -- band ---------------------------------------------------------------
  const band = document.createElement("section");
  band.className = "band";
  const readout = document.createElement("p");
  readout.id = "band-readout";
  band.appendChild(readout);
  const bar = document.createElement("div");
  bar.id = "allocation-bar";
  ["balance", "staked", "liquidity", "defi", "nft"].forEach((key) =>
    bar.appendChild(segment(key))
  );
  const figs = document.createElement("div");
  figs.className = "figs";
  figs.appendChild(fig("balance", 40));
  figs.appendChild(fig("staked", 30));
  figs.appendChild(fig("liquidity", 20));
  figs.appendChild(fig("defi", 10));
  figs.appendChild(fig("nft", 50));
  band.appendChild(bar);
  band.appendChild(figs);
  page.appendChild(band);

  // -- toolbar ------------------------------------------------------------
  const toolbar = document.createElement("div");
  toolbar.id = "toolbar";
  const field = document.createElement("input");
  field.id = "tb-q";
  field.type = "search";
  toolbar.appendChild(field);
  toolbar.setAttribute("data-floor", "2");
  toolbar.appendChild(seg("tb-group", "data-group", ["asset", "venue"], "asset"));
  toolbar.appendChild(
    seg("tb-sort", "data-sort", ["value", "amount", "name", "positions"], "value")
  );
  toolbar.appendChild(seg("tb-ccy", "data-ccy", ["ALGO", "USD"], "ALGO"));
  const direction = document.createElement("button");
  direction.id = "tb-dir";
  toolbar.appendChild(direction);
  const nonft = document.createElement("button");
  nonft.id = "tb-nonft";
  toolbar.appendChild(nonft);
  const refresh = document.createElement("button");
  refresh.id = "tb-refresh";
  toolbar.appendChild(refresh);
  const reset = document.createElement("button");
  reset.id = "tb-reset";
  toolbar.appendChild(reset);
  const status = document.createElement("p");
  status.id = "tb-status";
  toolbar.appendChild(status);
  page.appendChild(toolbar);

  // -- the list -----------------------------------------------------------
  const section = document.createElement("section");
  section.className = "section asasec";
  // What the server publishes: the first batch, and the size of every batch
  // after it.
  section.setAttribute("data-initial", "2");
  const sectionHead = document.createElement("div");
  sectionHead.className = "section-head";
  const heading = document.createElement("h2");
  heading.textContent = "Assets";
  const count = document.createElement("span");
  count.className = "count";
  count.textContent = "4";
  sectionHead.appendChild(heading);
  sectionHead.appendChild(count);
  section.appendChild(sectionHead);

  const list = document.createElement("div");
  list.className = "rows";
  list.id = "asset-list";
  list.setAttribute("data-folding", "");

  list.appendChild(
    card({
      id: "f1",
      unit: "AAA",
      value: 40,
      amount: 5,
      positions: 1,
      groups: [
        group({
          venue: "Wallet balance",
          asset: "AAA",
          positions: [position({ owner: "f1", cat: "balance", value: 40, search: "wallet aaa" })],
        }),
      ],
    })
  );
  list.appendChild(
    card({
      id: "f2",
      unit: "BBB",
      value: 30,
      amount: 900,
      positions: 1,
      groups: [
        group({
          venue: "Tinyman",
          asset: "BBB",
          href: "https://tinyman.org/",
          positions: [position({ owner: "f2", cat: "staked", value: 30, search: "tinyman bbb" })],
        }),
      ],
    })
  );
  list.appendChild(
    card({
      id: "f3",
      unit: "CCC",
      value: 20,
      amount: 70,
      positions: 2,
      groups: [
        group({
          venue: "Tinyman",
          asset: "CCC",
          positions: [position({ owner: "f3", cat: "liquidity", value: 20, search: "tinyman ccc" })],
        }),
      ],
    })
  );
  list.appendChild(
    card({
      id: "f4",
      unit: "DDD",
      value: 10,
      amount: 3,
      positions: 3,
      groups: [
        group({
          venue: "Folks",
          asset: "DDD",
          positions: [position({ owner: "f4", cat: "defi", value: 10, search: "folks ddd" })],
        }),
      ],
    })
  );
  section.appendChild(list);

  const venues = document.createElement("div");
  venues.className = "rows venue-rows";
  venues.id = "venue-list";
  venues.hidden = true;
  section.appendChild(venues);

  const more = document.createElement("div");
  const button = document.createElement("button");
  button.setAttribute("data-show-more", "");
  button.setAttribute("aria-expanded", "false");
  const label = document.createElement("span");
  label.className = "show-more-open";
  button.appendChild(label);
  more.appendChild(button);
  section.appendChild(more);

  page.appendChild(section);

  // The NFT section, as the money column renders it: collections are asset
  // cards in a `.rows` list, so the search reaches them the same way.
  const nft = document.createElement("section");
  nft.className = "section nftsec";
  nft.setAttribute("data-initial", "1");
  const nftRows = document.createElement("div");
  nftRows.className = "rows";
  nftRows.id = "nft-list";
  [
    ["fn1", "Brave New World"],
    ["fn2", "Poppin Puffins"],
  ].forEach(([id, name]) => {
    const collection = document.createElement("details");
    collection.className = "fitem mcard";
    collection.id = id;
    collection.setAttribute("data-search", name);
    nftRows.appendChild(collection);
  });
  nft.appendChild(nftRows);
  const nftMore = document.createElement("div");
  const nftButton = document.createElement("button");
  nftButton.setAttribute("data-show-more", "");
  const nftLabel = document.createElement("span");
  nftLabel.className = "show-more-open";
  nftButton.appendChild(nftLabel);
  nftMore.appendChild(nftButton);
  nft.appendChild(nftMore);
  page.appendChild(nft);

  document.body.appendChild(page);
}

/** Load toolbar.js against the current DOM and return what it exposes. */
function load() {
  jest.resetModules();
  delete require.cache[require.resolve("../static/js/toolbar.js")];
  // Nothing to un-bind: `toolbar.js` binds to the toolbar and the band, and
  // `mountPage` has just replaced both, so the previous test's handlers went
  // with the elements they were attached to. That is the whole reason it does
  // not delegate from `document` -- handlers there would accumulate one per
  // test, and the oldest would win every click.
  require("../static/js/toolbar.js");
  return window.asastatsToolbar;
}

/** Ids of the asset cards currently not filtered out, in DOM order. */
function visible() {
  return Array.prototype.slice
    .call(document.querySelectorAll("#asset-list > .fitem"))
    .filter((el) => !el.classList.contains("tb-hidden"))
    .map((el) => el.id);
}

/** Ids of the asset cards not folded away, in DOM order. */
function unfolded() {
  return Array.prototype.slice
    .call(document.querySelectorAll("#asset-list > .fitem"))
    .filter((el) => !el.classList.contains("tb-hidden") && !el.classList.contains("folded"))
    .map((el) => el.id);
}

beforeEach(() => {
  window.localStorage.clear();
  mountPage();
});

describe("what the toolbar shows on arrival", () => {
  test("an untouched page shows every asset and says nothing", () => {
    load();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
    expect(document.getElementById("tb-status").textContent).toBe("");
    expect(document.getElementById("tb-reset").disabled).toBe(true);
  });

  test("the served order is left alone until something is sorted", () => {
    // Value descending *is* the order the server rendered in, so there is
    // nothing to re-base and `pins.js` keeps whatever arrangement the reader
    // had. Re-basing anyway would quietly discard a dragged order on load.
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };

    load();

    expect(rebase).toHaveBeenCalledWith(expect.anything(), null);
  });

  test("a stored view is applied on load", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      JSON.stringify({ q: "bbb" })
    );

    load();

    expect(visible()).toEqual(["f2"]);
  });

  test("the reader's currency comes from its own key, not from this address", () => {
    // Design 1's key, deliberately. A reader who picks USD means USD, not "USD
    // on this address" -- and a second tab showing a different currency from
    // the first is what made this worth changing.
    window.localStorage.setItem("cur", "USD");

    load();

    expect(document.querySelector('#tb-ccy [data-ccy="USD"]').getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("4.00");
  });
});

describe("the search field", () => {
  test("typing narrows the list to what matches", () => {
    load();
    const field = document.getElementById("tb-q");

    field.value = "tinyman";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual(["f2", "f3"]);
  });

  test("a match on the asset keeps every position inside it", () => {
    // Typing a ticker should not require each row inside to repeat it.
    load();
    const field = document.getElementById("tb-q");

    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual(["f1"]);
    expect(
      document.querySelector('[data-owner="f1"]').classList.contains("tb-hidden")
    ).toBe(false);
  });

  test("clearing the field with the native control restores everything", () => {
    // Safari's search field fires `search`, not `input`, when its clear button
    // is used -- so a page bound only to `input` stays filtered with an empty
    // box, which looks like the filter is broken.
    load();
    const field = document.getElementById("tb-q");
    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));

    field.value = "";
    field.dispatchEvent(new window.Event("search"));

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("a query matching nothing empties the list rather than throwing", () => {
    load();
    const field = document.getElementById("tb-q");

    field.value = "zzzz";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual([]);
    expect(document.getElementById("tb-status").textContent).toBe(
      "Showing 0 of 4 assets."
    );
  });
});

describe("the category filter", () => {
  test("switching a category off hides its positions and its asset", () => {
    load();

    document.querySelector('.figs [data-band="staked"]').click();

    expect(visible()).toEqual(["f1", "f3", "f4"]);
  });

  test("the figure keeps reporting what the reader holds", () => {
    // Zeroing it would say "you have none" when what happened is "you hid it",
    // and a bar segment shrunk to nothing has no box left to click -- the
    // control would disable itself.
    load();
    const figure = document.querySelector('.figs [data-band="staked"]');

    figure.click();

    expect(figure.getAttribute("aria-pressed")).toBe("false");
    expect(figure.querySelector(".fig-val").textContent).toContain("30.00");
    // Its width is its share of all five categories, NFT included -- 30 of
    // 150 -- and switching it off changes neither.
    expect(
      document.querySelector('#allocation-bar [data-band="staked"]').style.width
    ).toBe("20%");
  });

  test("a bar segment toggles the same state the figure does", () => {
    load();

    document.querySelector('#allocation-bar [data-band="liquidity"]').click();

    expect(
      document.querySelector('.figs [data-band="liquidity"]').getAttribute("aria-pressed")
    ).toBe("false");
    expect(visible()).toEqual(["f1", "f2", "f4"]);
  });

  test("switching off the last category on turns the others back on", () => {
    // Otherwise the page empties with no obvious way back. A reader pressing
    // an already-solo category means "show me everything again".
    const toolbar = load();
    ["staked", "liquidity", "defi"].forEach((key) =>
      document.querySelector(`.figs [data-band="${key}"]`).click()
    );
    expect(visible()).toEqual(["f1"]);

    document.querySelector('.figs [data-band="balance"]').click();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
    expect(toolbar.state().cats).toHaveLength(4);
  });

  test("the NFT figure shows and hides the collections section", () => {
    load();

    document.querySelector('.figs [data-band="nft"]').click();

    expect(document.querySelector(".nftsec").hidden).toBe(true);

    document.querySelector('.figs [data-band="nft"]').click();

    expect(document.querySelector(".nftsec").hidden).toBe(false);
  });
});

describe("sorting", () => {
  test("value descending is the served order", () => {
    load();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("sorting by name hands pins.js a new baseline", () => {
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();

    document.querySelector('#tb-sort [data-sort="name"]').click();

    const order = rebase.mock.calls[rebase.mock.calls.length - 1][1].map((el) => el.id);
    expect(order).toEqual(["f4", "f3", "f2", "f1"]);
  });

  test("the direction control reverses it", () => {
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();
    document.querySelector('#tb-sort [data-sort="name"]').click();

    document.getElementById("tb-dir").click();

    const order = rebase.mock.calls[rebase.mock.calls.length - 1][1].map((el) => el.id);
    expect(order).toEqual(["f1", "f2", "f3", "f4"]);
    expect(document.getElementById("tb-dir").textContent).toBe("↑ Asc");
  });

  test("holdings sorts on the decimal-adjusted quantity", () => {
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();

    document.querySelector('#tb-sort [data-sort="amount"]').click();

    const order = rebase.mock.calls[rebase.mock.calls.length - 1][1].map((el) => el.id);
    expect(order).toEqual(["f2", "f3", "f1", "f4"]);
  });

  test("positions sorts on how many a card holds", () => {
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();

    document.querySelector('#tb-sort [data-sort="positions"]').click();

    const order = rebase.mock.calls[rebase.mock.calls.length - 1][1].map((el) => el.id);
    expect(order).toEqual(["f4", "f3", "f1", "f2"]);
  });

  test("ties break on the ticker rather than on where the row happened to be", () => {
    // Two assets worth exactly the same must come out in a defined order, or
    // they trade places whenever anything else re-renders and the list flickers
    // for no reason the reader can see. BBB is put *before* AAA in the document
    // and given the same value: a stable sort with no tie-break would leave it
    // there, so seeing AAA first is the tie-break doing the work.
    const list = document.getElementById("asset-list");
    list.insertBefore(document.getElementById("f2"), document.getElementById("f1"));
    document.getElementById("f2").setAttribute("data-sort-value", "40");
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();

    // Ascending, because descending *is* the served order and hands `pins.js`
    // a null baseline rather than a list.
    document.getElementById("tb-dir").click();

    const order = rebase.mock.calls[rebase.mock.calls.length - 1][1].map((el) => el.id);
    expect(order).toEqual(["f4", "f3", "f1", "f2"]);
  });

  test("a page without pins.js sorts without throwing", () => {
    delete window.asastatsPins;
    load();

    expect(() =>
      document.querySelector('#tb-sort [data-sort="name"]').click()
    ).not.toThrow();
  });
});


describe("currency", () => {
  test("switching to USD converts every figure and every unit", () => {
    load();

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    const value = document.querySelector("#f1 .cval .val");
    expect(value.textContent.trim()).toBe("4.00");
    expect(document.querySelector("#f1 .cval .u.unit").textContent).toBe("USD");
  });

  test("a subtotal keeps its own unit element", () => {
    // `address.js`'s setCurrency writes innerHTML including the unit, which
    // destroys the nested span here and leaves the asset header reading
    // "4.00 USD USD" beside its sibling. This writer touches the number only.
    load();

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    const total = document.querySelector("#f1 .pgroup-total");
    expect(total.querySelectorAll(".unit")).toHaveLength(1);
    expect(total.querySelector(".unit").textContent).toBe("USD");
    expect(total.textContent.trim()).toBe("4.00 USD");
  });

  test("switching back restores ALGO", () => {
    load();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    document.querySelector('#tb-ccy [data-ccy="ALGO"]').click();

    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("40.00");
    expect(document.querySelector("#f1 .cval .u.unit").textContent).toBe("ALGO");
  });

  test("a figure too small for two decimals widens instead of rounding to nothing", () => {
    // A borrowing of -0.004055 ALGO is real, and "0.00" reads as nothing owed.
    const toolbar = load();

    expect(toolbar.fmt(-0.004055)).toBe("-0.004055");
    expect(toolbar.fmt(0)).toBe("0.00");
  });

  test("a page whose header carries no rate leaves figures alone", () => {
    document.querySelector(".pricetip").removeAttribute("data-pricealgo");
    const toolbar = load();
    toolbar.state(Object.assign(toolbar.state(), { ccy: "USD" }));

    expect(toolbar.fmt(40)).toBe("0.00");
  });

  test("a value element with no text node still receives its figure", () => {
    const toolbar = load();
    const element = document.createElement("span");

    toolbar.write(element, 12.5);

    expect(element.textContent).toBe("12.50");
  });

  test("a negative figure is marked as one", () => {
    const toolbar = load();
    const element = document.createElement("span");

    toolbar.write(element, -3);

    expect(element.classList.contains("neg")).toBe(true);
  });
});

describe("grouping by venue", () => {
  test("every group moves into the venue that holds it", () => {
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    const cards = Array.prototype.slice.call(
      document.querySelectorAll("#venue-list > .venue-card")
    );
    expect(cards.map((el) => el.getAttribute("data-venue-card"))).toEqual([
      "Wallet balance",
      "Tinyman",
      "Folks",
    ]);
    expect(document.getElementById("asset-list").hidden).toBe(true);
  });

  test("the rows are moved, not copied, so a pid names one row", () => {
    document
      .querySelector('[data-owner="f2"]')
      .setAttribute("data-pid", "p1-2-abc");
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    expect(document.querySelectorAll('[data-pid="p1-2-abc"]')).toHaveLength(1);
  });

  test("a venue card totals what it holds", () => {
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    const tinyman = document.querySelector('[data-venue-card="Tinyman"]');
    expect(tinyman.querySelector(".venue-total").textContent).toBe("50.00");
  });

  test("a linked venue keeps its link on the card", () => {
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    const link = document
      .querySelector('[data-venue-card="Tinyman"]')
      .querySelector(".cid-name a");
    expect(link).not.toBeNull();
    expect(link.href).toBe("https://tinyman.org/");
  });

  test("the section renames itself and counts venues", () => {
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    expect(document.querySelector(".asasec .section-head h2").textContent).toBe("Venues");
    expect(document.querySelector(".asasec .section-head .count").textContent).toBe("3");
    expect(document.getElementById("tb-status").textContent).toBe(
      "Showing 3 of 3 venues."
    );
  });

  test("switching back puts every group where the server had it", () => {
    load();
    const before = Array.prototype.slice
      .call(document.querySelectorAll("#asset-list .pgroup"))
      .map((el) => el.getAttribute("data-asset"));

    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-group [data-group="asset"]').click();

    const after = Array.prototype.slice
      .call(document.querySelectorAll("#asset-list .pgroup"))
      .map((el) => el.getAttribute("data-asset"));
    expect(after).toEqual(before);
    expect(document.getElementById("venue-list").childElementCount).toBe(0);
    expect(document.querySelector(".asasec .section-head h2").textContent).toBe("Assets");
  });

  test("an asset holding several venues gets them back in order", () => {
    // The bug this replaced: the restore remembered each group's *sibling*, and
    // an asset with four venues had all four moved away -- so putting the first
    // one back threw, because the node it was to be inserted before had gone.
    const holder = document.querySelector("#f1 .program-groups");
    ["Tinyman", "Folks", "Pact"].forEach((venue) =>
      holder.appendChild(
        group({
          venue,
          asset: "AAA",
          positions: [position({ owner: "f1", cat: "defi", value: 1, search: venue })],
        })
      )
    );
    load();
    const before = Array.prototype.slice
      .call(document.querySelectorAll("#f1 .pgroup"))
      .map((el) => el.getAttribute("data-venue"));

    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-group [data-group="asset"]').click();

    const after = Array.prototype.slice
      .call(document.querySelectorAll("#f1 .pgroup"))
      .map((el) => el.getAttribute("data-venue"));
    expect(after).toEqual(before);
  });

  test("filtering while grouped by venue empties the cards it excludes", () => {
    load();
    document.querySelector('#tb-group [data-group="venue"]').click();

    const field = document.getElementById("tb-q");
    field.value = "folks";
    field.dispatchEvent(new window.Event("input"));

    const hidden = Array.prototype.slice
      .call(document.querySelectorAll("#venue-list > .venue-card"))
      .filter((el) => el.classList.contains("tb-hidden"))
      .map((el) => el.getAttribute("data-venue-card"));
    expect(hidden).toEqual(["Wallet balance", "Tinyman"]);
  });

  test("a page with no venue list leaves the grouping alone", () => {
    document.getElementById("venue-list").remove();
    const toolbar = load();

    expect(() => toolbar.regroup()).not.toThrow();
  });
});

describe("reset", () => {
  test("it puts everything back and disables itself", () => {
    load();
    const field = document.getElementById("tb-q");
    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));
    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();
    expect(document.getElementById("tb-reset").disabled).toBe(false);

    document.getElementById("tb-reset").click();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
    expect(document.getElementById("venue-list").hidden).toBe(true);
    expect(document.getElementById("tb-q").value).toBe("");
    expect(document.getElementById("tb-reset").disabled).toBe(true);
  });

  test("it leaves the reader's own settings alone", () => {
    // Currency, auto-refresh and "without NFTs" follow the reader across
    // addresses and tabs. "Reset view" undoes what they did to *this* page --
    // resetting their currency because they cleared a filter would be a
    // control reaching outside what it says it does.
    load();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();
    document.getElementById("tb-nonft").click();

    document.getElementById("tb-reset").click();

    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("4.00");
    expect(document.getElementById("tb-nonft").getAttribute("aria-pressed")).toBe("true");
  });

  test("it brings the NFT section back", () => {
    load();
    document.querySelector('.figs [data-band="nft"]').click();

    document.getElementById("tb-reset").click();

    expect(document.querySelector(".nftsec").hidden).toBe(false);
  });

  test("resetting forgets the stored view rather than storing the defaults", () => {
    const toolbar = load();
    const field = document.getElementById("tb-q");
    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));
    expect(window.localStorage.getItem(toolbar.viewKey())).not.toBeNull();

    document.getElementById("tb-reset").click();

    expect(window.localStorage.getItem(toolbar.viewKey())).toBeNull();
  });
});

describe("the stored view", () => {
  test("it survives a reload", () => {
    load();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    mountPage();
    load();

    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("4.00");
  });

  test("a value no longer offered falls back without losing the rest", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      JSON.stringify({ sort: "gone", more: { asa: "x" }, dir: 1, group: "venue" })
    );

    const toolbar = load();

    expect(toolbar.state().sort).toBe("value");
    expect(toolbar.state().more.asa).toBe(0);
    expect(toolbar.state().dir).toBe(1);
    expect(toolbar.state().group).toBe("venue");
  });

  test("a reader who switched every category off is not handed them back", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      JSON.stringify({ cats: [] })
    );

    const toolbar = load();

    expect(toolbar.state().cats).toEqual([]);
    expect(visible()).toEqual([]);
  });

  test("stored nonsense is ignored rather than thrown", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      "{not json"
    );

    const toolbar = load();

    expect(toolbar.state().sort).toBe("value");
  });

  test("a stored value that is not an object is ignored", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      '"a string"'
    );

    const toolbar = load();

    expect(toolbar.state().ccy).toBe("ALGO");
  });

  test("a store that refuses to be written costs persistence, not the page", () => {
    const setItem = window.localStorage.setItem;
    window.localStorage.setItem = () => {
      throw new Error("QuotaExceededError");
    };
    load();

    expect(() => {
      const field = document.getElementById("tb-q");
      field.value = "aaa";
      field.dispatchEvent(new window.Event("input"));
    }).not.toThrow();
    expect(visible()).toEqual(["f1"]);

    window.localStorage.setItem = setItem;
  });

  test("a store that refuses to be read falls back to the defaults", () => {
    const getItem = window.localStorage.getItem;
    window.localStorage.getItem = () => {
      throw new Error("SecurityError");
    };

    const toolbar = load();

    expect(toolbar.state().ccy).toBe("ALGO");
    window.localStorage.getItem = getItem;
  });
});

describe("the charts panel", () => {
  test("an open panel is redrawn from the filtered totals", () => {
    const panel = document.createElement("details");
    panel.id = "charts";
    panel.open = true;
    document.querySelector(".money-page").appendChild(panel);
    const redraw = jest.fn();
    window.asastatsMoney = { redrawAllocation: redraw };
    load();

    document.querySelector('.figs [data-band="staked"]').click();

    const totals = redraw.mock.calls[redraw.mock.calls.length - 1][0];
    expect(totals.staked).toBe(30);
  });

  test("a closed panel is not redrawn", () => {
    const panel = document.createElement("details");
    panel.id = "charts";
    panel.open = false;
    document.querySelector(".money-page").appendChild(panel);
    const redraw = jest.fn();
    window.asastatsMoney = { redrawAllocation: redraw };
    load();

    expect(redraw).not.toHaveBeenCalled();
  });

  test("a page without money.js does not try to redraw", () => {
    delete window.asastatsMoney;
    load();

    expect(() =>
      document.querySelector('.figs [data-band="defi"]').click()
    ).not.toThrow();
  });
});

describe("when the script arrives before the document", () => {
  test("it waits for DOMContentLoaded rather than finding nothing", () => {
    Object.defineProperty(document, "readyState", {
      value: "loading",
      configurable: true,
    });
    load();
    // Nothing has run yet, so the reader's stored view has not been applied.
    expect(window.asastatsToolbar.state()).toBeNull();

    document.dispatchEvent(new window.Event("DOMContentLoaded"));

    expect(window.asastatsToolbar.state()).not.toBeNull();
    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
    Object.defineProperty(document, "readyState", {
      value: "complete",
      configurable: true,
    });
  });
});

describe("binding", () => {
  test("a page with no toolbar is left alone", () => {
    document.getElementById("toolbar").remove();

    expect(() => load()).not.toThrow();
    expect(window.asastatsToolbar.state()).toBeNull();
  });

  test("a second execution does not bind a second set of handlers", () => {
    // Two handlers would toggle a category on and straight back off, which
    // looks exactly like a dead control.
    load();
    require("../static/js/toolbar.js");

    document.querySelector('.figs [data-band="staked"]').click();

    expect(visible()).toEqual(["f1", "f3", "f4"]);
  });

  test("a click on the toolbar's own chrome does nothing", () => {
    // The status line and the labels are inside the bound container, so the
    // handler runs for them and has to decline.
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });

    document.getElementById("tb-status").dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("a click on something else is left to whoever wants it", () => {
    load();
    const stray = document.createElement("button");
    document.body.appendChild(stray);

    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    stray.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
  });

  test("a click already handled elsewhere is not handled twice", () => {
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    event.preventDefault();

    document.querySelector('.figs [data-band="staked"]').dispatchEvent(event);

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("a band control outside the band and the toolbar is ignored", () => {
    // Nothing is listening out there, which is the point of binding to the two
    // containers rather than to the document.
    load();
    const stray = document.createElement("button");
    stray.setAttribute("data-band", "staked");
    document.body.appendChild(stray);

    stray.click();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("a page whose field is missing still binds the rest", () => {
    document.getElementById("tb-q").remove();
    load();

    expect(() =>
      document.querySelector('#tb-sort [data-sort="name"]').click()
    ).not.toThrow();
  });
});

describe("a page missing the parts it can do without", () => {
  /**
   * Every guard in `toolbar.js` exists because this page is assembled from
   * five templates and two other scripts, and a design that drops one element
   * must not take the whole toolbar with it -- a reader would lose filtering,
   * sorting and the currency switch because a subtotal span was renamed.
   *
   * Driven rather than asserted one guard at a time: what matters is that the
   * controls still work, not which line returned early.
   */
  function drive() {
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();
    document.querySelector('.figs [data-band="staked"]').click();
    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-group [data-group="asset"]').click();
  }

  test("no price on the header leaves every figure in ALGO terms", () => {
    document.querySelector(".pricetip").remove();
    const toolbar = load();
    toolbar.state(Object.assign(toolbar.state(), { ccy: "USD" }));

    expect(toolbar.fmt(40)).toBe("0.00");
  });

  test("a row with no search text is simply never a match", () => {
    document.querySelector('[data-owner="f1"]').removeAttribute("data-search");
    document.getElementById("f1").removeAttribute("data-search");
    load();
    const field = document.getElementById("tb-q");

    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual([]);
  });

  test("a card with no sortable name sorts to one end without throwing", () => {
    document.getElementById("f3").removeAttribute("data-sort-name");
    document.getElementById("f4").removeAttribute("data-sort-name");
    const rebase = jest.fn();
    window.asastatsPins = { rebase, apply: jest.fn() };
    load();

    expect(() =>
      document.querySelector('#tb-sort [data-sort="name"]').click()
    ).not.toThrow();
  });

  test("a card with no value cell still filters and totals", () => {
    document.querySelector("#f1 .cval .val").remove();
    load();

    expect(() => drive()).not.toThrow();
    expect(visible()).toEqual(["f1", "f3", "f4"]);
  });

  test("a group with no subtotal or count still hides when it empties", () => {
    document.querySelector("#f2 .pgroup-total").remove();
    document.querySelector("#f2 .pgroup-name .n").remove();
    load();

    document.querySelector('.figs [data-band="staked"]').click();

    expect(document.querySelector("#f2 .pgroup").classList.contains("tb-hidden")).toBe(true);
  });

  test("a band with no figure values still presses its controls", () => {
    document.querySelectorAll(".figs .fig-val").forEach((el) => el.remove());
    document.querySelectorAll(".figs .fig-share").forEach((el) => el.remove());
    load();

    document.querySelector('.figs [data-band="defi"]').click();

    expect(
      document.querySelector('.figs [data-band="defi"]').getAttribute("aria-pressed")
    ).toBe("false");
  });

  test("a toolbar with no direction, reset or status still filters", () => {
    ["tb-dir", "tb-reset", "tb-status"].forEach((id) =>
      document.getElementById(id).remove()
    );
    load();
    const field = document.getElementById("tb-q");

    field.value = "bbb";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual(["f2"]);
  });

  test("a toolbar missing a whole segmented group leaves the others alone", () => {
    document.getElementById("tb-sort").remove();
    load();

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("4.00");
  });

  test("a page with no NFT section ignores the NFT figure", () => {
    document.querySelector(".nftsec").remove();
    load();

    expect(() => document.querySelector('.figs [data-band="nft"]').click()).not.toThrow();
    expect(() => document.getElementById("tb-reset").click()).not.toThrow();
  });

  test("a page with no band binds the toolbar anyway", () => {
    document.querySelector(".band").remove();
    load();
    const field = document.getElementById("tb-q");

    field.value = "ccc";
    field.dispatchEvent(new window.Event("input"));

    expect(visible()).toEqual(["f3"]);
  });

  test("a section with no heading still switches grouping", () => {
    document.querySelector(".asasec .section-head").remove();
    load();

    expect(() =>
      document.querySelector('#tb-group [data-group="venue"]').click()
    ).not.toThrow();
    expect(document.getElementById("venue-list").childElementCount).toBe(3);
  });

  test("a venue card whose total was removed still counts its rows", () => {
    load();
    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('[data-venue-card="Tinyman"] .venue-total').remove();

    expect(() => window.asastatsToolbar.render()).not.toThrow();
  });

  test("switching to venues twice remembers each group's first home", () => {
    // The second switch must not re-record where a group sits, because by then
    // it sits wherever the previous switch put it.
    load();
    const before = Array.prototype.slice
      .call(document.querySelectorAll("#asset-list .pgroup"))
      .map((el) => el.getAttribute("data-venue"));

    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-group [data-group="asset"]').click();
    document.querySelector('#tb-group [data-group="venue"]').click();
    document.querySelector('#tb-group [data-group="asset"]').click();

    const after = Array.prototype.slice
      .call(document.querySelectorAll("#asset-list .pgroup"))
      .map((el) => el.getAttribute("data-venue"));
    expect(after).toEqual(before);
  });

  test("a group with no home is left where it is rather than lost", () => {
    load();
    document.querySelector('#tb-group [data-group="venue"]').click();
    const orphan = document.querySelector("#venue-list .pgroup");
    delete orphan._asastatsHome;

    document.querySelector('#tb-group [data-group="asset"]').click();

    expect(document.querySelectorAll(".pgroup")).toHaveLength(4);
  });

  test("a click whose target cannot be walked up from is ignored", () => {
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "target", { value: {}, configurable: true });

    expect(() => document.getElementById("toolbar").dispatchEvent(event)).not.toThrow();
  });
});

describe("values the markup did not supply", () => {
  test("a stored view can turn the NFT section off", () => {
    window.localStorage.setItem(
      "view:" + window.location.pathname.replace(/^\/+|\/+$/g, ""),
      JSON.stringify({ nft: false })
    );

    load();

    expect(document.querySelector(".nftsec").hidden).toBe(true);
  });

  test("a figure that is not a number counts as nothing", () => {
    document.querySelector('[data-owner="f1"]').setAttribute("data-value", "n/a");
    load();

    expect(document.querySelector("#f1 .cval .val").textContent.trim()).toBe("0.00");
  });

  test("a position with no category is treated as DeFi", () => {
    // Where `position_band` puts anything it does not recognise, so the row
    // stays in the picture instead of vanishing from every category at once.
    document.querySelector('[data-owner="f1"]').removeAttribute("data-cat");
    load();

    document.querySelector('.figs [data-band="defi"]').click();

    expect(visible()).toEqual(["f2", "f3"]);
  });

  test("a group with no venue is the wallet balance", () => {
    document.querySelector("#f2 .pgroup").removeAttribute("data-venue");
    load();

    document.querySelector('#tb-group [data-group="venue"]').click();

    expect(
      document.querySelector('[data-venue-card="Wallet balance"]').querySelectorAll(".pgroup")
    ).toHaveLength(2);
  });

  test("switching a category back on adds only that one", () => {
    const toolbar = load();
    document.querySelector('.figs [data-band="staked"]').click();

    document.querySelector('.figs [data-band="staked"]').click();

    expect(toolbar.state().cats.sort()).toEqual([
      "balance",
      "defi",
      "liquidity",
      "staked",
    ]);
  });

  test("restoring the assets on a page with no venue list does nothing", () => {
    const toolbar = load();
    document.getElementById("venue-list").remove();

    expect(() => toolbar.toAssets()).not.toThrow();
  });

  test("a page grouped by venue with no venue list counts no venues", () => {
    // The status line asks the venue list how many it is showing, and the
    // grouping switch has already declined to do anything -- so it has to
    // answer without one rather than throw on a page that is still usable.
    const toolbar = load();
    document.querySelector('#tb-group [data-group="venue"]').click();
    document.getElementById("venue-list").remove();

    expect(() => toolbar.render()).not.toThrow();
    expect(document.getElementById("tb-status").textContent).toBe(
      "Showing 0 of 0 venues."
    );
  });
});

describe("the load-more control", () => {
  test("a section without one still folds its tail", () => {
    document.querySelector(".asasec [data-show-more]").parentNode.remove();
    const toolbar = load();

    expect(unfolded()).toEqual(["f1", "f2"]);
  });

  test("a control without a label is left with the label it has", () => {
    document.querySelector(".asasec .show-more-open").remove();
    const toolbar = load();

    expect(() => toolbar.render()).not.toThrow();
    expect(
      document.querySelector(".asasec [data-show-more]").parentNode.hidden
    ).toBe(false);
  });
});


describe("the search and the NFT section", () => {
  /** Ids of the collections a reader can see. */
  function collections() {
    return Array.prototype.slice
      .call(document.querySelectorAll("#nft-list > .fitem"))
      .filter((el) => !el.classList.contains("tb-hidden"))
      .map((el) => el.id);
  }

  test("a query narrows the collections too", () => {
    // Filtering for a collection's name and being shown every collection
    // beside three matching assets is not filtering the page.
    load();
    const field = document.getElementById("tb-q");

    field.value = "brave";
    field.dispatchEvent(new window.Event("input"));

    expect(collections()).toEqual(["fn1"]);
  });

  test("the category filter leaves them alone", () => {
    // A collection is not a position and has no category. The NFT band is what
    // shows and hides this section, and it does it wholesale.
    load();

    document.querySelector('.figs [data-band="staked"]').click();

    expect(collections()).toEqual(["fn1", "fn2"]);
  });

  test("clearing the query brings them back", () => {
    load();
    const field = document.getElementById("tb-q");
    field.value = "brave";
    field.dispatchEvent(new window.Event("input"));

    field.value = "";
    field.dispatchEvent(new window.Event("input"));

    expect(collections()).toEqual(["fn1", "fn2"]);
  });
});

describe("the load-more rule", () => {
  /**
   * A plain count, not the prototype's 95%/99%/99.5%/All. That control was a
   * way to *demonstrate* the page with everything on screen before a load-more
   * existed; "show me the rows carrying 99.5% of the value" is not a sentence a
   * reader thinks in. The mounted page publishes 2 assets and 1 collection per
   * batch, which is the four-asset fixture's version of 20 and 10.
   */
  test("a section shows its first batch and offers the next", () => {
    load();

    expect(unfolded()).toEqual(["f1", "f2"]);
    expect(document.querySelector(".asasec .show-more-open").textContent).toBe(
      "Show 2 more assets"
    );
  });

  test("a press adds one batch, not the whole tail", () => {
    load();

    document.querySelector(".asasec [data-show-more]").click();

    expect(unfolded()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("the label promises only what the press delivers", () => {
    // "Show 56 more" over a control that reveals twenty is a lie the reader
    // finds out about by pressing it.
    const list = document.getElementById("asset-list");
    ["f5", "f6", "f7"].forEach((id) =>
      list.appendChild(
        card({
          id,
          unit: id.toUpperCase(),
          value: 1,
          amount: 1,
          positions: 1,
          groups: [
            group({
              venue: "Wallet balance",
              asset: id,
              positions: [position({ owner: id, cat: "balance", value: 1 })],
            }),
          ],
        })
      )
    );
    load();

    expect(document.querySelector(".asasec .show-more-open").textContent).toBe(
      "Show 2 more assets"
    );
  });

  test("the last batch names what is actually left", () => {
    load();
    // Four assets, batches of two: one press leaves nothing.
    document.querySelector(".asasec [data-show-more]").click();

    expect(document.querySelector(".asasec [data-show-more]").parentNode.hidden).toBe(true);
  });

  test("one row left over is singular", () => {
    const list = document.getElementById("asset-list");
    list.appendChild(
      card({
        id: "f5",
        unit: "EEE",
        value: 1,
        amount: 1,
        positions: 1,
        groups: [
          group({
            venue: "Wallet balance",
            asset: "EEE",
            positions: [position({ owner: "f5", cat: "balance", value: 1 })],
          }),
        ],
      })
    );
    load();
    document.querySelector(".asasec [data-show-more]").click();

    expect(document.querySelector(".asasec .show-more-open").textContent).toBe(
      "Show 1 more asset"
    );
  });

  test("the collections have their own count and their own control", () => {
    load();

    expect(
      Array.prototype.slice
        .call(document.querySelectorAll("#nft-list > .fitem"))
        .filter((el) => !el.classList.contains("folded")).length
    ).toBe(1);
    expect(document.querySelector(".nftsec .show-more-open").textContent).toBe(
      "Show 1 more collection"
    );

    document.querySelector(".nftsec [data-show-more]").click();

    expect(
      Array.prototype.slice
        .call(document.querySelectorAll("#nft-list > .fitem"))
        .filter((el) => !el.classList.contains("folded")).length
    ).toBe(2);
  });

  test("the two sections count separately", () => {
    // One press on the assets must not reveal collections, and the reverse.
    load();

    document.querySelector(".asasec [data-show-more]").click();

    expect(
      Array.prototype.slice
        .call(document.querySelectorAll("#nft-list > .fitem"))
        .filter((el) => !el.classList.contains("folded")).length
    ).toBe(1);
  });

  test("how far a reader had scrolled survives a reload", () => {
    load();
    document.querySelector(".asasec [data-show-more]").click();

    mountPage();
    load();

    expect(unfolded()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("reset folds the sections back", () => {
    load();
    document.querySelector(".asasec [data-show-more]").click();

    document.getElementById("tb-reset").click();

    expect(unfolded()).toEqual(["f1", "f2"]);
  });

  test("a section that publishes no count shows one row rather than none", () => {
    // A missing attribute is a template that changed; showing one row is
    // recoverable by pressing, showing none looks like an empty address.
    document.querySelector(".asasec").removeAttribute("data-initial");
    load();

    expect(unfolded()).toEqual(["f1"]);
  });
});

describe("the headline", () => {
  /** The `.pricetip` text, which is the total. */
  function headline() {
    return document.querySelector(".pricetip").textContent;
  }

  test("it follows the currency", () => {
    // The figure no *filter* may move -- but a currency is not a filter, it is
    // the unit the whole page is denominated in. A page whose every figure says
    // USD above a total that says ALGO is not showing a total at all.
    load();
    expect(headline()).toBe("150.00 ALGO");

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    expect(headline()).toBe("15.00 USD");
  });

  test("no filter moves it", () => {
    load();

    document.querySelector('.figs [data-band="defi"]').click();
    const field = document.getElementById("tb-q");
    field.value = "aaa";
    field.dispatchEvent(new window.Event("input"));

    expect(headline()).toBe("150.00 ALGO");
  });

  test("without NFTs takes them out of it", () => {
    // Which is a change to *what is being totalled*, not to how it is shown.
    load();

    document.getElementById("tb-nonft").click();

    expect(headline()).toBe("100.00 ALGO");
    expect(document.querySelector(".total-note").textContent).toContain("except the NFTs");
  });

  test("the line under it shows the other currency", () => {
    load();

    expect(document.querySelector(".total-sub .num").textContent).toContain("15.00 USD");
  });

  test("the tooltip carries the other currency too", () => {
    load();

    expect(document.querySelector(".pricetip").getAttribute("data-tip")).toBe("15.00 USD");
  });

  test("a page with no headline renders the rest", () => {
    document.querySelector(".total").remove();
    load();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });
});

describe("the band readout", () => {
  /** What the readout says. */
  function readout() {
    return document.getElementById("band-readout").textContent;
  }

  test("an unfiltered page says nothing", () => {
    // Telling a reader that their total is their total is noise.
    load();

    expect(readout()).toBe("");
  });

  test("switching a category off says what the rest comes to", () => {
    // The headline stays at the whole address, which is right and also leaves
    // the reader no way to see what they are actually looking at.
    load();

    document.querySelector('.figs [data-band="defi"]').click();

    expect(readout()).toBe("Showing 140.00 ALGO of 150.00 ALGO");
  });

  test("hiding the NFTs counts them out of it too", () => {
    load();

    document.querySelector('.figs [data-band="nft"]').click();

    expect(readout()).toBe("Showing 100.00 ALGO of 150.00 ALGO");
  });

  test("it is denominated like everything else", () => {
    load();
    document.querySelector('.figs [data-band="defi"]').click();

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    expect(readout()).toBe("Showing 14.00 USD of 15.00 USD");
  });

  test("switching the category back on clears it", () => {
    load();
    document.querySelector('.figs [data-band="defi"]').click();

    document.querySelector('.figs [data-band="defi"]').click();

    expect(readout()).toBe("");
  });

  test("a page without one renders the rest", () => {
    document.getElementById("band-readout").remove();
    load();

    expect(() => document.querySelector('.figs [data-band="defi"]').click()).not.toThrow();
  });
});

describe("the reader's own settings", () => {
  test("auto-refresh writes the key address.js already watches", () => {
    // The timer is running there whatever this page does; writing the key is
    // the whole implementation.
    load();

    document.getElementById("tb-refresh").click();

    expect(window.localStorage.getItem("refresh")).toBe("y");
    expect(document.getElementById("tb-refresh").getAttribute("aria-pressed")).toBe("true");
  });

  test("switching it off leaves the key falsy rather than truthy", () => {
    // `address.js` reads this key and reloads the page when it says "y", so
    // "off" has to be something that is not "y" -- the exact value is the
    // store's business, and jest's mock and a browser disagree about whether an
    // empty string reads back as "" or null.
    load();
    document.getElementById("tb-refresh").click();

    document.getElementById("tb-refresh").click();

    expect(window.localStorage.getItem("refresh") || "").not.toBe("y");
    expect(document.getElementById("tb-refresh").getAttribute("aria-pressed")).toBe("false");
  });

  test("they come back on the next page in design 1's keys", () => {
    load();
    document.getElementById("tb-nonft").click();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    expect(window.localStorage.getItem("totalnonft")).toBe("y");
    expect(window.localStorage.getItem("cur")).toBe("USD");
  });

  test("they are not written into this address's view", () => {
    // One setting with two homes is one setting that can disagree with itself.
    const toolbar = load();
    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    const stored = JSON.parse(window.localStorage.getItem(toolbar.viewKey()) || "{}");
    expect(stored.ccy).toBeUndefined();
  });

  test("a store that refuses to be written still switches the page", () => {
    const setItem = window.localStorage.setItem;
    window.localStorage.setItem = () => {
      throw new Error("QuotaExceededError");
    };
    load();

    expect(() => document.getElementById("tb-nonft").click()).not.toThrow();

    window.localStorage.setItem = setItem;
  });

  test("a store that refuses to be read falls back to the defaults", () => {
    // Both reads have to survive it: the per-address view is parsed inside its
    // own try, and the reader-level keys are read separately afterwards.
    const getItem = window.localStorage.getItem;
    window.localStorage.getItem = () => {
      throw new Error("SecurityError");
    };

    const toolbar = load();

    expect(toolbar.state().ccy).toBe("ALGO");
    expect(toolbar.state().nonft).toBe(false);
    expect(toolbar.state().refresh).toBe(false);
    window.localStorage.getItem = getItem;
  });
});

describe("a page missing the parts the headline and the fold need", () => {
  test("a venue view whose asset control is gone still switches", () => {
    load();
    document.querySelector(".asasec [data-show-more]").parentNode.remove();

    expect(() =>
      document.querySelector('#tb-group [data-group="venue"]').click()
    ).not.toThrow();
  });

  test("a headline with no sub-line or note still switches currency", () => {
    document.querySelector(".total-sub").remove();
    document.querySelector(".total-note").remove();
    load();

    document.querySelector('#tb-ccy [data-ccy="USD"]').click();

    expect(document.querySelector(".pricetip").textContent).toBe("15.00 USD");
  });

  test("an address worth nothing divides by nothing rather than by zero", () => {
    document.querySelectorAll("[data-value]").forEach((el) => el.setAttribute("data-value", "0"));
    document.querySelectorAll(".fig-val").forEach((el) => el.setAttribute("data-val", "0"));
    load();

    expect(
      document.querySelector('#allocation-bar [data-band="balance"]').style.width
    ).toBe("0%");
    expect(document.querySelector('.figs [data-band="balance"] .fig-share').textContent).toBe("0.0%");
  });

  test("a toolbar with no toggles still renders", () => {
    document.getElementById("tb-nonft").remove();
    document.getElementById("tb-refresh").remove();
    load();

    expect(visible()).toEqual(["f1", "f2", "f3", "f4"]);
  });

  test("a show-more press already handled elsewhere is not counted twice", () => {
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    event.preventDefault();

    document.querySelector(".asasec [data-show-more]").dispatchEvent(event);

    expect(unfolded()).toEqual(["f1", "f2"]);
  });
});

describe("a page whose sections are not there", () => {
  test("no asset section leaves the rest working", () => {
    // `fold` is asked about a section by name; a page that lost one must not
    // take the collections and the band down with it.
    document.querySelector(".asasec").remove();
    load();

    expect(document.querySelector(".pricetip").textContent).toBe("150.00 ALGO");
  });

  test("a click on a section that is not the control is ignored", () => {
    load();

    document.querySelector(".asasec").click();

    expect(unfolded()).toEqual(["f1", "f2"]);
  });

  test("a click whose target cannot be walked up from is ignored there too", () => {
    load();
    const event = new window.MouseEvent("click", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "target", { value: {}, configurable: true });

    expect(() => document.querySelector(".asasec").dispatchEvent(event)).not.toThrow();
  });
});
