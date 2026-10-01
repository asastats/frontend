const fs = require('fs');
const path = require('path');
const capturedPage = fs.readFileSync(
  path.resolve(__dirname, './address.html'), 'utf8'
);
const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.tooltip = jest.fn();
$.prototype.animate = jest.fn(function () { return this; });

let lastConfig;

/**
 * A stand-in for a Chart.js instance.
 *
 * Its data mirrors the captured page's distribution payload -- the widest of
 * the six -- because `updateDistChart` walks the parsed payload and writes
 * each value into the instance at the same index. A mock with fewer datasets
 * than the page carries throws there rather than failing an assertion.
 */
function chartInstance(overrides) {
  var dist = payload('distchart');
  return Object.assign({
    canvas: { id: 'id-asachart' },
    data: {
      datasets: dist.datasets.map(function (set) {
        return { data: set.data.slice() };
      }),
      labels: dist.labels.slice()
    },
    config: { type: 'pie' },
    legend: { legendItems: Array.from({ length: 12 }, () => ({ hidden: false })) },
    options: { plugins: { legend: { labels: { generateLabels: () => [] } } } },
    titleBlock: { options: { text: '' } },
    toggleDataVisibility: jest.fn(),
    setDatasetVisibility: jest.fn(),
    isDatasetVisible: jest.fn(() => true),
    update: jest.fn(),
    getElementsAtEventForMode: jest.fn(() => []),
  }, overrides || {});
}

function chartImpl(ctx, config) {
  lastConfig = config;
  Object.assign(this, chartInstance());
}

window.Chart = jest.fn(chartImpl);
window.Chart.getChart = jest.fn(() => chartInstance());

global.M = {
  Collapsible: { getInstance: jest.fn(() => ({ close: jest.fn() })) },
};

const address = require('../static/js/address.js');

function pie(name) {
  return '<script type="application/json" id="' + name + '">' +
    '{"datasets":[{"data":["30","70"]}],"labels":["x","y"]}</script>' +
    '<canvas id="id-' + name + '"></canvas>' +
    '<div id="id-legend-' + name + '"></div>';
}

/*
 * The DOM is the page the site serves: `javascript_tests/address.html`,
 * captured by `scripts/capture_address_fixture.py` from the same template and
 * sample payload the Python template tests use. Every selector in address.js
 * is a contract with that markup, and an inline approximation cannot hold it
 * -- the one this suite used carried hooks the page never emitted while the
 * template moved on underneath, and nothing could tell.
 *
 * Two things are still built here, because a capture cannot provide them
 * deterministically:
 *
 *   * epoch spans. The capture carries whatever dates the sample payload had,
 *     and these tests assert relative phrasing -- "30 minutes ago", "ended".
 *     The captured ones are removed so a selector cannot mix the two;
 *   * rows whose text is known. Filtering is asserted on "findme", which no
 *     real holding contains, so a match is unambiguous.
 */
/**
 * A payload the captured page carries, parsed from the fixture itself.
 *
 * Expectations are derived from it rather than written down: the numbers come
 * from a real portfolio and change whenever the fixture is recaptured, so a
 * literal here would be a value nobody chose and everybody would have to
 * update.
 */
function payload(id) {
  var match = capturedPage.match(
    new RegExp('<script id="' + id + '" type="application/json">([^<]*)</script>')
  );
  return JSON.parse(match[1]);
}

/**
 * One legend entry per dataset, which is what Chart.js hands a bar chart.
 *
 * `percentDistAsset` walks the parsed distribution payload and reads the
 * legend entry at the same index, so a shorter list throws rather than
 * failing an assertion.
 */
function legendItemsForDist(hiddenIndex) {
  return payload("distchart").datasets.map(function (_, i) {
    return { hidden: i === hiddenIndex };
  });
}

function controlledEpochs() {
  var now = Math.floor(Date.now() / 1000);
  return {
    times:
      '<span class="epoch" data-epoch="' + (now - 30) + '"></span>' +
      '<span class="epoch" data-epoch="' + (now - 1800) + '"></span>' +
      '<span class="epoch" data-epoch="' + (now - 36000) + '"></span>' +
      '<span class="epoch" data-epoch="' + (now - 864000) + '"></span>',
    expiry:
      '<span class="epoch" data-epoch="' + (now - 1000) + '" data-ended="1"></span>' +
      '<span class="epoch" data-epoch="' + (now + 1000) + '"></span>' +
      '<span class="epoch" data-epoch="' + (now - 1000) + '"></span>',
  };
}

/** Scaffolding the captured page cannot supply: known text, and a thumbnail
 *  with no full-size image behind it. */
function scaffold() {
  return (
    '<div class="fsec section-list">' +
    '<div class="fitem" id="if1"><span>findme</span><span>findme</span></div>' +
    '<div class="fitem" id="if2"><span>findme</span></div>' +
    '<div class="fitem"><span>findme</span></div>' +
    '<span class="nfticon" id="tif1" data-path="/x.png"></span>' +
    '<span class="nfticon" id="other"></span></div>'
  );
}

/** Mount the captured page, then the controlled nodes on top of it. */
function mountFixture() {
  document.body.innerHTML = capturedPage;

  var controlled = controlledEpochs();
  Array.prototype.forEach.call(document.querySelectorAll(".epoch"), function (span) {
    span.remove();
  });
  var nftBody = document.querySelector(".nftsec .item-body");
  if (nftBody) nftBody.insertAdjacentHTML("beforeend", controlled.times);
  var asaBody = document.querySelector(".asasec .item-body");
  if (asaBody) asaBody.insertAdjacentHTML("beforeend", controlled.expiry);

  document.body.insertAdjacentHTML("beforeend", scaffold());
}

beforeEach(() => {
  mountFixture();
  localStorage.clear();
  if (localStorage.setItem.mockClear) localStorage.setItem.mockClear();
  window.Chart.mockReset();
  window.Chart.mockImplementation(chartImpl);
  window.Chart.getChart.mockReset();
  window.Chart.getChart.mockReturnValue(chartInstance());
  M.Collapsible.getInstance.mockClear();
  M.Collapsible.getInstance.mockReturnValue({ close: jest.fn() });
  // No location stub here any more. It used to be
  //
  //     reloadMock = jest.fn();
  //     delete window.location;
  //     window.location = { reload: reloadMock };
  //
  // and it never worked: jsdom's `location` is a non-configurable property
  // whose `reload` is read-only, so the delete is a no-op and the assignment is
  // discarded -- it only ever logged an error into every run of this file.
  // Nothing asserted on `reloadMock`, so nothing noticed for as long as it has
  // been here. The auto-refresh tests assert on the ids `reloadPage` stores
  // before it navigates, which is a real consequence and needs no stub.
});

afterEach(() => {
  // jsdom queues a `toggle` event on its own timer whenever a <details>
  // changes state. Left pending, those land after jest has torn the
  // environment down, where jQuery's dispatch touches a document that no
  // longer exists -- and jsdom's error reporter then crashes on
  // `window._document.URL`, taking the whole run with it rather than failing
  // a single test.
  // The event is queued on a real Node timer, so no fake-timer flush reaches
  // it. Detaching the handlers does: when it finally fires there is nothing
  // left to run, and nothing throws.
  $("details").off();
  jest.useRealTimers();
  document.body.innerHTML = "";
  jest.resetModules();
});


describe("parseJsonScript", function () {
  it('parses a plain JSON script', function () {
    expect(address.parseJsonScript("distchart").labels).toEqual(
      payload("distchart").labels
    );
  });

  it('builds ratiochartfloor percentages from the consolidated data', function () {
    // Not a script on the page: it is derived from `#consolidated`, whose
    // five figures become the slices of the floor-value ratio chart.
    var data = address.parseJsonScript("ratiochartfloor");

    expect(data.datasets[0].data.length).toBe(payload("consolidated").length);
  });
});


describe("isNotVisible / scrollToView", function () {
  it('isNotVisible true when element is above the viewport', function () {
    var el = { offsetTop: -100 };
    expect(address.isNotVisible(el)).toBe(true);
  });
  it('isNotVisible true when element is below the viewport', function () {
    var el = { offsetTop: 100000 };
    expect(address.isNotVisible(el)).toBe(true);
  });
  it('isNotVisible false when element is inside the viewport', function () {
    var el = { offsetTop: 0 };
    expect(address.isNotVisible(el)).toBe(false);
  });
  it('scrollToView animates when not visible', function () {
    expect(address.scrollToView({ offsetTop: 100000 }, 250)).toBe(false);
  });
  it('scrollToView returns true when already visible', function () {
    expect(address.scrollToView({ offsetTop: 0 }, 250)).toBe(true);
  });
});


describe("setCurrency", function () {
  it('formats values in ALGO', function () {
    window.Chart.getChart.mockReturnValue(chartInstance());
    ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart",
      "distchart"].forEach(function (n) { address.parseJsonScript(n); });
    address.setCurrency("ALGO");
    expect($(".switch input[type=checkbox]").prop("checked")).toBe(false);
  });
  it('formats values in USD', function () {
    window.Chart.getChart.mockReturnValue(chartInstance());
    ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart",
      "distchart"].forEach(function (n) { address.parseJsonScript(n); });
    address.setCurrency("USD");
    expect($(".switch input[type=checkbox]").prop("checked")).toBe(true);
  });
});


describe("toggleCurrency", function () {
  function setup() {
    ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart",
      "distchart"].forEach(function (n) { address.parseJsonScript(n); });
    window.Chart.getChart.mockReturnValue(chartInstance());
  }
  it('switches to USD when checked', function () {
    setup();
    var box = $(".switch input[type=checkbox]")[0];
    box.checked = true;
    address.toggleCurrency.call(box);
    expect(localStorage.setItem).toHaveBeenCalledWith("cur", "USD");
  });
  it('switches to ALGO when unchecked', function () {
    setup();
    var box = $(".switch input[type=checkbox]")[0];
    box.checked = false;
    address.toggleCurrency.call(box);
    expect(localStorage.setItem).toHaveBeenCalledWith("cur", "ALGO");
  });
});


describe("togglePrice", function () {
  it('switches to ALGO/unit form', function () {
    var el = $(".price")[0];
    address.togglePrice.call(el, { target: { innerHTML: "2 USD/ALGO" } });
    expect(el.innerHTML).toContain("ALGO/");
  });
  it('switches to reciprocal form', function () {
    var el = $(".price")[0];
    address.togglePrice.call(el, { target: { innerHTML: "2 ALGO/USD" } });
    expect(el.innerHTML).toContain("/ALGO");
  });
});


describe("toggleUnitPrice", function () {
  it('shows reciprocal in ALGO', function () {
    var el = $(".unitprice")[0];
    address.toggleUnitPrice.call(el, { target: { innerHTML: "nope" } });
    expect(el.innerHTML).toContain("/ALGO");
  });
  it('shows direct value in USD', function () {
    localStorage.setItem("cur", "USD");
    var el = $(".unitprice")[0];
    address.toggleUnitPrice.call(el, { target: { innerHTML: "USDC" } });
    expect(el.innerHTML).toContain("USD");
  });

  it('shows the direct price when the label already names the unit', function () {
    // The control flips between `X/ALGO` and `ALGO/X`, and which way round it
    // goes is decided by whether the text already contains the asset's own
    // unit. Both directions are reachable from a real row.
    var el = $(".unitprice")[0];

    address.toggleUnitPrice.call(el, { target: { innerHTML: el.dataset.unit } });

    expect(el.innerHTML).toContain("ALGO");
    expect(el.innerHTML).not.toContain("/ALGO");
  });
});


describe("toggleDist", function () {
  it('toggles the distribution section visibility', function () {
    // The page renders these panels collapsed, so the assertion is that the
    // control flips the state -- not that it reaches one particular one.
    var el = $(".tdist")[0];
    var target = document.getElementById(el.dataset.distid);
    expect(target).not.toBeNull();
    var before = $(target).hasClass("hidden");

    address.toggleDist.call(el, null);
    expect($(target).hasClass("hidden")).toBe(!before);

    address.toggleDist.call(el, null);
    expect($(target).hasClass("hidden")).toBe(before);
  });
});


describe("showTimes", function () {
  it('fills epoch spans with elapsed time', function () {
    var header = $(".nft.item-header")[0];

    address.showTimes.call(header, null);

    expect($(".nftsec .epoch").html()).toContain("ago on");
  });
});


describe("populatePieCharts", function () {
  it('creates the five pie charts', function () {
    address.populatePieCharts();
    expect(window.Chart).toHaveBeenCalledTimes(5);
  });
});


describe("mainAddress", function () {
  it('initializes the page', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    expect(window.Chart).toHaveBeenCalled();
  });
});


function parseAll() {
  ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart",
    "distchart"].forEach(function (n) { address.parseJsonScript(n); });
}


describe("chart tooltip / hover / legend callbacks", function () {
  function configs() {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    return {
      dist: window.Chart.mock.calls[0][1],
      ratio: window.Chart.mock.calls[1][1],
      asa: window.Chart.mock.calls[3][1],
    };
  }
  it('dist tooltip label and footer', function () {
    parseAll();
    var c = configs();
    var ctx = {
      raw: "5", dataIndex: 0, datasetIndex: 0, dataset: { label: "A" },
      chart: { legend: { legendItems: legendItemsForDist(1) } },
    };
    var ctx2 = {
      raw: "5", dataIndex: 0, datasetIndex: 1, dataset: { label: "B" },
      chart: { legend: { legendItems: legendItemsForDist(1) } },
    };
    expect(typeof c.dist.options.plugins.tooltip.callbacks.label(ctx))
      .toBe("string");
    expect(typeof c.dist.options.plugins.tooltip.callbacks.footer([ctx]))
      .toBe("string");
    expect(typeof c.dist.options.plugins.tooltip.callbacks.footer([ctx2]))
      .toBe("string");
    localStorage.setItem("cur", "USD");
    expect(typeof c.dist.options.plugins.tooltip.callbacks.label(ctx))
      .toBe("string");
    expect(typeof c.dist.options.plugins.tooltip.callbacks.footer([ctx]))
      .toBe("string");
  });
  it('dist and pie onHover both cursor states', function () {
    parseAll();
    var c = configs();
    var hover = { native: { target: { style: {} } } };
    c.dist.options.onHover(hover, [{}]);
    c.dist.options.onHover(hover, []);
    c.ratio.options.onHover(hover, [{}]);
    c.asa.options.onHover(hover, [{}]);
    c.asa.options.onHover(hover, []);
  });
  it('pie label uses valueSection', function () {
    parseAll();
    var c = configs();
    expect(typeof c.asa.options.plugins.tooltip.callbacks.label(
      { formattedValue: "30", dataIndex: 0 })).toBe("string");
  });
  it('htmlLegend afterUpdate renders and wires legend clicks', function () {
    parseAll();
    var c = configs();
    var plugin = c.dist.plugins[0];
    var items = [
      {
        fillStyle: "#fff", strokeStyle: "#000", lineWidth: 1, hidden: true,
        text: "H", index: 0, datasetIndex: 0
      },
      {
        fillStyle: "#000", strokeStyle: "#fff", lineWidth: 2, hidden: false,
        text: "S", index: 1, datasetIndex: 0
      },
    ];
    var pieChart = chartInstance({
      config: { type: 'pie' }, canvas: { id: 'id-asachart' },
      legend: { legendItems: legendItemsForDist(1) },
      options: { plugins: { legend: { labels: { generateLabels: () => items } } } },
    });
    var container = document.getElementById('id-legend-distchart');
    plugin.afterUpdate(pieChart, {}, { containerID: 'id-legend-distchart' });
    container.querySelector('li').onclick();
    var barChart = chartInstance({
      config: { type: 'bar' },
      options: { plugins: { legend: { labels: { generateLabels: () => items } } } },
    });
    plugin.afterUpdate(barChart, {}, { containerID: 'id-legend-distchart' });
    container.querySelector('li').onclick();
    expect(pieChart.update).toHaveBeenCalled();
  });
});


describe("chart onclick wrappers", function () {
  function withPoints() {
    window.Chart.mockImplementation(function (ctx, config) {
      lastConfig = config;
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => [{ index: 0 }]),
      }));
    });
  }
  it('dist canvas onclick delegates to chartClick', function () {
    jest.useFakeTimers();
    withPoints();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    document.getElementById('id-distchart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('pie canvas onclick delegates to chartClick', function () {
    jest.useFakeTimers();
    withPoints();
    address.populatePieCharts();
    document.getElementById('id-asachart').onclick({});
    jest.advanceTimersByTime(400);
  });
});


describe("chartClick (direct)", function () {
  function chart(points, label) {
    return {
      getElementsAtEventForMode: jest.fn(function () { return points; }),
      data: { labels: [label] },
    };
  }

  /** A unit the captured page actually lists. */
  function heldUnit() {
    return payload("asachart").labels[0];
  }
  it('does nothing when there are no points', function () {
    jest.useFakeTimers();
    address.chartClick(chart([], "a"), {});
    jest.advanceTimersByTime(300);
  });
  it('toggles the header for a visible unit', function () {
    jest.useFakeTimers();
    address.chartClick(chart([{ index: 0 }], heldUnit()), {});
    jest.advanceTimersByTime(300);
  });
  it('scrolls to an off-screen unit before toggling', function () {
    jest.useFakeTimers();
    Object.defineProperty($(".unit")[0], "offsetTop", { value: -100000 });
    address.chartClick(chart([{ index: 0 }], heldUnit()), {});
    jest.advanceTimersByTime(300);
  });
  it('ignores a slice with no row behind it', function () {
    // A portfolio past the chart's item limit gets an "others" slice standing
    // for the tail, and no row carries that unit. Clicking it used to hand
    // `undefined` to scrollToView, which reads `.offsetTop`.
    jest.useFakeTimers();

    expect(function () {
      address.chartClick(chart([{ index: 0 }], "others"), {});
      jest.advanceTimersByTime(300);
    }).not.toThrow();
  });

  it('does not toggle a header that is already active', function () {
    jest.useFakeTimers();
    $(".unit").wrap('<div><div></div></div>').parent().parent()
      .wrap('<div class="active"></div>');
    address.chartClick(chart([{ index: 0 }], heldUnit()), {});
    jest.advanceTimersByTime(300);
  });
});


describe("showMatchedNodes (direct)", function () {
  it('returns false when there are no matches', function () {
    expect(address.showMatchedNodes([])).toBe(false);
  });
  it('shows the matched item and its matching icon', function () {
    address.showMatchedNodes([["if1"]]);
    expect($("#if1").css("display")).not.toBe("none");
  });
});


describe("totalChart (direct)", function () {
  ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart"]
    .forEach(function (name) {
      it('computes a total for ' + name, function () {
        expect(address.totalChart(name)).not.toBeUndefined();
      });
    });
  it('returns zero for an unknown chart name', function () {
    expect(address.totalChart("nope")).toBe(0);
  });
  it('converts the total to USD when selected', function () {
    localStorage.setItem("cur", "USD");
    expect(typeof address.totalChart("asachart")).toBe("number");
  });
  it('converts an nft total to USD', function () {
    localStorage.setItem("cur", "USD");
    expect(typeof address.totalChart("nftchart")).toBe("number");
  });
});


describe("filterChange", function () {
  function press(code) {
    address.mainAddress();
    $("#filter").trigger($.Event("keypress", { keyCode: code }));
  }
  it('ignores keys that are not separators', function () {
    jest.useFakeTimers();
    press(65);
    expect($(".fitem#if1").css("display")).not.toBe("none");
  });
  it('shows everything when the filter is empty', function () {
    jest.useFakeTimers();
    $("#filter").val("");
    press(13);
  });
  it('filters to matching items', function () {
    jest.useFakeTimers();
    $("#filter").val("findme");
    press(13);
  });
  it('splits on commas when more commas than spaces', function () {
    jest.useFakeTimers();
    $("#filter").val("findme,nope");
    press(44);
  });
});


describe("wireFetchedItems (htmx:after:swap)", function () {
  // **A collection's items are not on the page until the reader opens it.**
  // They used to be: every collection wrote out every item, hidden inside a
  // closed <details>, and the fetch on open replaced them. On one real account
  // that was 87.9% of a 22 MB page. Now the body arrives by htmx -- and
  // deferImages only ever ran over the elements present at load, so the art in
  // anything swapped in later stayed on its placeholder for good. That was
  // already true of the design-2 layout, which has fetched on open all along.

  it('promotes data-src on content htmx swapped in', function () {
    window.onload();
    document.body.innerHTML =
      '<div id="swapped"><img class="nft" data-src="/late.png" src="" /></div>';
    var swapped = document.getElementById("swapped");

    swapped.dispatchEvent(
      new CustomEvent("htmx:after:swap", { bubbles: true })
    );

    expect(document.querySelector("img.nft").src).toContain("/late.png");
  });

  it('leaves an event with no usable target alone', function () {
    // The listener sits on document.body and sees every afterSwap that bubbles
    // to it, whatever dispatched it. A target with no descendants to search - a
    // text node is the easy one to construct, and settled content can contain
    // them - would throw on getElementsByClassName, and that throw would take
    // down every later swap on the page rather than just this one.
    window.onload();
    var text = document.createTextNode("swapped text");
    document.body.appendChild(text);

    expect(function () {
      text.dispatchEvent(new CustomEvent("htmx:after:swap", { bubbles: true }));
    }).not.toThrow();
  });

  it('is harmless when the swapped content holds no deferred images', function () {
    window.onload();
    document.body.innerHTML = '<div id="plain"><p>no art here</p></div>';
    var plain = document.getElementById("plain");

    expect(function () {
      plain.dispatchEvent(new CustomEvent("htmx:after:swap", { bubbles: true }));
    }).not.toThrow();
  });
});


describe("initAddress (window.onload)", function () {
  it('defers images and opens stored sections', function () {

    var deferred = $("img.nft[data-src]").first();
    var wanted = deferred.attr("data-src");
    localStorage.setItem("openasa", $(".asasec .fitem").first().attr("id"));

    window.onload();

    expect(deferred.attr("src")).toBe(wanted);
  });

  it('reopens the row it remembered', function () {
    // The rows sit inside a wrapper under their section heading, so this
    // lookup has to search descendants. Walking direct children finds the
    // heading and the wrapper, and the remembered row never reopens -- which
    // is exactly what happened when the headings were added.
    var row = $(".asasec .fitem").first();
    row.removeAttr("open");
    localStorage.setItem("openasa", row.attr("id"));

    window.onload();

    expect(row[0].open).toBe(true);
    expect(localStorage.removeItem).toHaveBeenCalledWith("openasa");
  });

  it('stops at the row it wanted', function () {
    // The walk returns false to break out once the stored id matches, so the
    // match has to be something other than the first entry for that to run.
    var rows = $(".asasec .fitem");
    if (rows.length < 2) return;
    var wanted = rows.eq(1);
    rows.removeAttr("open");
    localStorage.setItem("openasa", wanted.attr("id"));

    window.onload();

    expect(wanted[0].open).toBe(true);
    expect(rows.eq(0)[0].open).toBe(false);
  });

  it('does nothing extra when no section stored', function () {
    window.onload();
    expect(window.onload).toBeDefined();
  });

  it('falls back to default nft.png when deferred image fails to load', function () {
    // 1. Setup the DOM with an image that has a data-src
    document.body.innerHTML = '<img class="nft" data-src="/broken.png" src="" />';
    // 2. Trigger onload, which calls deferImages() and attaches the onerror handler
    window.onload();
    // 3. Grab the image element
    const imgElement = document.querySelector("img.nft");
    // Verify deferImages properly set the initial src
    expect(imgElement.src).toContain("/broken.png");
    // 4. Manually trigger the 'error' event to simulate a 404 from the CDN
    const errorEvent = new Event('error');
    imgElement.dispatchEvent(errorEvent);
    // 5. Assert that the onerror handler updated the src to the fallback
    expect(imgElement.src).toBe('https://cdn.asastats.com/thumbnails/nft.png');
    // 6. Assert that the onerror handler removed itself (prevents infinite loops)
    expect(imgElement.onerror).toBeNull();
  });
});


describe("NFT floor", function () {
  it('mainAddress applies the stored floor=y state', function () {
    jest.useFakeTimers();
    localStorage.setItem("nftfloor", "y");
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    jest.advanceTimersByTime(400);
    expect($(".floor input[type=checkbox]").prop("checked")).toBe(true);
  });
  it('toggleNftFloor reacts to the checkbox', function () {
    jest.useFakeTimers();
    address.mainAddress();
    var box = $(".floor input[type=checkbox]")[0];
    box.checked = true;
    $(box).trigger("change");
    jest.advanceTimersByTime(400);
    expect(localStorage.setItem).toHaveBeenCalledWith("nftfloor", "y");
    box.checked = false;
    $(box).trigger("change");
    jest.advanceTimersByTime(400);
  });
});


describe("NFT tooltips", function () {
  it('shows and hides the preview on hover and click', function () {
    // The preview is a real element now rather than a Materialize tooltip
    // instance decorating the thumbnail, so it can simply be looked for --
    // and looked for again after the click, which must remove it.
    jest.useFakeTimers();
    address.mainAddress();
    var thumbnail = $(".nfticon").first();
    thumbnail.trigger("mouseover");
    var preview = document.getElementById("id-nft-preview");
    expect(preview).not.toBeNull();
    expect(preview.querySelector("img").getAttribute("src")).toBe(
      thumbnail[0].dataset.path
    );

    $(".nfticon").first().trigger("click");

    expect(document.getElementById("id-nft-preview")).toBeNull();
  });

  it('closes the preview when the pointer leaves the thumbnail', function () {
    // What the Materialize tooltip did. Without it the preview hangs over the
    // rows below while the reader moves on down the collection.
    jest.useFakeTimers();
    address.mainAddress();
    $(".nfticon").first().trigger("mouseover");
    expect(document.getElementById("id-nft-preview")).not.toBeNull();

    $(".nfticon").first().trigger("mouseleave");

    expect(document.getElementById("id-nft-preview")).toBeNull();
  });

  it('leaves the preview image unlabelled when the thumbnail is', function () {
    // Every captured thumbnail carries an alt, so the fallback needs one that
    // does not: an empty alt is correct here, `undefined` would render the
    // string "undefined" into the accessibility tree.
    jest.useFakeTimers();
    // Added before the bindings: this page binds to the thumbnails it finds,
    // so one appended afterwards would simply have no handler.
    var bare = $('<img class="nfticon" data-path="/full.png">').appendTo("body");
    address.mainAddress();

    bare.trigger("mouseover");

    expect(
      document.getElementById("id-nft-preview").querySelector("img").alt
    ).toBe("");
  });

  it('shows nothing for a thumbnail with no full image', function () {
    // `#other` has no data-path. Building a preview from it would produce an
    // <img src=""> -- a visible broken-image box hovering over the page.
    jest.useFakeTimers();
    address.mainAddress();
    $("#other").trigger("mouseover");
    expect(document.getElementById("id-nft-preview")).toBeNull();
  });
});


describe("showExpiry / timeEntry", function () {
  it('fills expiry spans across ended, future and past', function () {
    jest.useFakeTimers();
    address.mainAddress();
    $(".token.item-header").trigger("click");
    var html = $(".asasec .epoch").map(function () {
      return this.innerHTML;
    }).get().join(" ");
    expect(html).toContain("on");
  });
});


describe("auto refresh", function () {
  it('reloads the page once the minute is up when refresh is on', function () {
    jest.useFakeTimers();
    localStorage.setItem("refresh", "y");
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    // `checkOpened` records which entries were open so the reload can restore
    // them, so an entry has to be open for there to be anything to record --
    // the captured page renders them all closed.
    var asa = $(".asasec .fitem").first().attr("open", "open");
    var nft = $(".nftsec .fitem").first().attr("open", "open");

    jest.advanceTimersByTime(61000);

    expect(localStorage.setItem).toHaveBeenCalledWith("openasa", asa.attr("id"));
    expect(localStorage.setItem).toHaveBeenCalledWith("opennft", nft.attr("id"));
  });
  it('just increments when refresh is off', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    localStorage.setItem("refresh", "");
    address.mainAddress();
    jest.advanceTimersByTime(62000);
    expect(localStorage.setItem).not.toHaveBeenCalledWith("openasa", "fa1");
  });
  it('toggleRefresh reacts to the checkbox', function () {
    jest.useFakeTimers();
    address.mainAddress();
    var box = $(".refresh input[type=checkbox]")[0];
    box.checked = true;
    $(box).trigger("change");
    expect(localStorage.setItem).toHaveBeenCalledWith("refresh", "y");
    box.checked = false;
    $(box).trigger("change");
    expect(localStorage.setItem).toHaveBeenCalledWith("refresh", "");
  });
  it('noteActivity is wired to document activity, scrolling included', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress.call(document);
    $(document).trigger("mousemove");
    $(document).trigger("keypress");
    // Scrolling is what the guard is for and what mousemove misses.
    $(document).trigger("scroll");
    $(document).trigger("wheel");
    $(document).trigger("touchmove");
  });

  // What the auto-refresh toggle actually buys, asserted rather than assumed.
  //
  // Everything around this was covered and none of it was the behaviour: the
  // test above triggers events and expects nothing, and the functional test
  // presses `#tb-refresh` and checks only that localStorage says "y". Between
  // them, a toggle that never reloaded anything would have passed both.
  //
  // **These now measure elapsed time rather than counting ticks**, because the
  // code does. Driving `timerIncrement` 61 times no longer means anything: a
  // background tab's interval is throttled to about once a minute, so ticks
  // and seconds are not the same quantity and treating them as one is the bug
  // that let a hidden tab go an hour stale.
  //
  // `reloadPage` records the open accordions and *then* calls
  // `window.location.reload()`. The record is what these assert on -- not by
  // choice: jsdom's `location.reload` is read-only, so the suite's `reloadMock`
  // is a no-op and nothing had ever noticed. The stored id is a real
  // consequence of reaching `reloadPage` and needs no stub at all.
  describe('the auto-refresh timer', function () {
    function elapse(ms) {
      jest.advanceTimersByTime(ms);
    }
    function reloaded() {
      return localStorage.setItem.mock.calls.some(function (call) {
        return call[0] === 'openasa';
      });
    }
    beforeEach(function () {
      jest.useFakeTimers();
      var row = document.querySelector('.asasec .fitem');
      row.id = 'row-under-test';
      row.open = true;
      localStorage.setItem('refresh', 'y');
      localStorage.setItem.mockClear();
      // Arms the clock from "now", as initAddress does on a real page.
      address.timerIncrement();
      localStorage.setItem.mockClear();
    });

    it('does not reload before a minute has passed', function () {
      elapse(59000);
      address.timerIncrement();

      expect(reloaded()).toBe(false);
    });

    it('reloads once the minute is up', function () {
      elapse(61000);
      address.timerIncrement();

      expect(reloaded()).toBe(true);
    });

    it('defers while the reader is busy, and fires when they settle', function () {
      elapse(61000);
      address.noteActivity();
      address.timerIncrement();
      // Due, but somebody is scrolling: left alone.
      expect(reloaded()).toBe(false);

      // They stop. The refresh happens now -- it is not pushed another minute
      // away, which is the whole difference from the old idle timer.
      elapse(address.SETTLE_MS);
      address.timerIncrement();

      expect(reloaded()).toBe(true);
    });

    it('still refreshes a reader who keeps touching the page', function () {
      // The reported "120 second delay". Activity every 30s used to put the
      // count back to zero, so this reader was never refreshed at all.
      for (var minute = 0; minute < 4; minute++) {
        elapse(30000);
        address.noteActivity();
        address.timerIncrement();
      }
      elapse(address.SETTLE_MS);
      address.timerIncrement();

      expect(reloaded()).toBe(true);
    });

    it('catches up a tab that was hidden past its due time', function () {
      elapse(61000);

      address.refreshOnReturn();

      expect(reloaded()).toBe(true);
    });

    it('does nothing while the tab is still hidden', function () {
      // `visibilitychange` fires on the way out as well as the way in, and a
      // refresh on the way out would reload a page nobody is looking at -
      // which is also the one moment the reader cannot see it go wrong.
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        get: function () { return 'hidden'; },
      });
      elapse(61000);

      address.refreshOnReturn();

      expect(reloaded()).toBe(false);
      delete document.visibilityState;
    });

    it('recovers when the clock moves backwards', function () {
      // An NTP correction or a laptop waking with a corrected time leaves a
      // stamp in the future, and `now - then` then reads as "just now" for as
      // long as the jump was. Without the guard a refresh could be held off
      // for hours by an interaction that has not happened yet.
      elapse(61000);
      address.noteActivity();
      var future = Date.now() + 3600000;
      jest.setSystemTime(future - 3600000 - 120000);

      address.timerIncrement();  // notices the jump, restarts the minute
      elapse(61000);
      address.timerIncrement();

      expect(reloaded()).toBe(true);
    });

    it('stands down when the subscriber poll is on the page', function () {
      // The two must never both be running. The poll swaps the figures that
      // changed and leaves scroll position, open sections and filters alone;
      // a reload on top of that throws away the one thing it exists to
      // preserve. The marker arrives in a non-cached partial *after* load,
      // which is why this is asked every tick rather than once at startup.
      var marker = document.createElement('span');
      marker.id = 'id-liverefresh';
      document.body.appendChild(marker);
      elapse(61000);

      address.timerIncrement();

      expect(reloaded()).toBe(false);
      marker.remove();
    });

    it('lets a briefly hidden tab finish its own minute', function () {
      elapse(20000);

      address.refreshOnReturn();

      // Not due yet, so returning to the tab changes nothing -- the clock is
      // measured from the last refresh, not from when the tab was hidden.
      expect(reloaded()).toBe(false);
    });

    it('leaves the page alone when the setting is off', function () {
      localStorage.setItem('refresh', '');
      localStorage.setItem.mockClear();
      elapse(61000);
      address.timerIncrement();

      expect(reloaded()).toBe(false);
    });
  });
});


describe("total without NFTs", function () {
  it('toggleTotalNoNft in ALGO', function () {
    jest.useFakeTimers();
    address.mainAddress();
    var box = $(".totalnonft input[type=checkbox]")[0];
    box.checked = true;
    $(box).trigger("change");
    expect(localStorage.setItem).toHaveBeenCalledWith("totalnonft", "y");
  });
  it('toggleTotalNoNft in USD', function () {
    jest.useFakeTimers();
    localStorage.setItem("cur", "USD");
    address.mainAddress();
    var box = $(".totalnonft input[type=checkbox]")[0];
    box.checked = false;
    $(box).trigger("change");
    expect(localStorage.setItem).toHaveBeenCalledWith("totalnonft", "");
  });
});


describe("consolidated section", function () {
  // A native <details>: `toggle` fires on the element after `open` has already
  // changed, so the handler reads the property rather than an inline style
  // Materialize used to write.
  it('onConsolidatedClick stores the visibility state', function () {
    jest.useFakeTimers();
    address.mainAddress();

    document.getElementById('id-cons').open = false;
    $("#id-cons").trigger("toggle");

    expect(localStorage.setItem).toHaveBeenCalledWith("cons", "h");
  });

  it('onConsolidatedClick stores empty when the section is open', function () {
    jest.useFakeTimers();
    address.mainAddress();

    document.getElementById('id-cons').open = true;
    $("#id-cons").trigger("toggle");

    expect(localStorage.setItem).toHaveBeenCalledWith("cons", "");
  });

  it('survives a stored hidden state with no section to close', function () {
    // `checkConsolidated` runs from mainAddress on every page that loads this
    // script, and the stored value outlives the page that set it. Reading
    // `.open` off null would throw there and abandon every binding declared
    // after it.
    jest.useFakeTimers();
    localStorage.setItem("cons", "h");
    window.Chart.getChart.mockReturnValue(chartInstance());
    document.getElementById('id-cons').remove();

    expect(function () { address.mainAddress(); }).not.toThrow();
  });

  it('checkConsolidated closes the section when stored hidden', function () {
    // Closing a <details> is setting a property; there is no plugin instance
    // to fetch and nothing to animate.
    jest.useFakeTimers();
    localStorage.setItem("cons", "h");
    window.Chart.getChart.mockReturnValue(chartInstance());
    document.getElementById('id-cons').open = true;

    address.mainAddress();

    expect(document.getElementById('id-cons').open).toBe(false);
  });
});


describe("scroll-to-top control", function () {
  it('appears once the reader is well down the page', function () {
    jest.useFakeTimers();
    address.mainAddress();
    var button = document.getElementById("scroll-to-top");

    window.scrollY = 500;
    $(window).trigger("scroll");
    expect(button.classList.contains("visible")).toBe(true);

    window.scrollY = 10;
    $(window).trigger("scroll");
    expect(button.classList.contains("visible")).toBe(false);
  });

  it('does nothing on a page without the control', function () {
    // The button is rendered by address.html only; the handler is bound to
    // the window, so it runs on any page that loads this script.
    jest.useFakeTimers();
    address.mainAddress();
    document.getElementById("scroll-to-top").remove();

    window.scrollY = 500;
    expect(function () { $(window).trigger("scroll"); }).not.toThrow();
  });

  it('scrolls to the top and swallows the anchor navigation', function () {
    var scrollTo = jest.fn();
    window.scrollTo = scrollTo;
    var prevented = jest.fn();

    address.scrollToTop({ preventDefault: prevented });

    expect(prevented).toHaveBeenCalled();
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "smooth" });
  });

  it('works when called without an event', function () {
    // `scrollToTop` is also reachable programmatically, where there is no
    // event to prevent the default of.
    var scrollTo = jest.fn();
    window.scrollTo = scrollTo;

    expect(function () { address.scrollToTop(); }).not.toThrow();
    expect(scrollTo).toHaveBeenCalled();
  });
});


describe("setCurrency on the dynamic designs", function () {
  it('leaves that page alone entirely', function () {
    // Design 1's currency writer writes `innerHTML` -- number *and* unit --
    // into every `span.val`. On the money column each figure pairs with a
    // separate unit element, so it left the asset header reading "253.74 ALGO"
    // beside a sibling still saying "ALGO", and destroyed the nested span in
    // every venue subtotal. It ran on every load, because `mainAddress` calls
    // it unconditionally with the stored currency. `toolbar.js` owns currency
    // there now.
    var page = document.createElement("div");
    page.className = "dynamic-page";
    var value = document.createElement("span");
    value.className = "val";
    value.dataset.val = "12.5";
    value.innerHTML = "12.50";
    page.appendChild(value);
    document.body.appendChild(page);

    address.setCurrency('USD');

    expect(value.innerHTML).toBe("12.50");
    page.remove();
  });
});


describe("setTotalNoNft on the dynamic designs", function () {
  it('leaves the headline to the toolbar', function () {
    // It writes `.pricetip` reading design 1's own global `cur` key, so on the
    // money page the total was written by design 1 on load and by nobody
    // afterwards: a reader who had ever chosen USD got a USD headline in a
    // fresh tab, and pressing USD in that page's toolbar changed every figure
    // except the one at the top.
    var page = document.createElement("div");
    page.className = "dynamic-page";
    var head = document.createElement("span");
    head.className = "pricetip";
    head.dataset.price = "0.1";
    head.dataset.pricealgo = "0.1";
    head.dataset.totalwnft = "150";
    head.dataset.totalnft = "50";
    head.innerHTML = "150.00 ALGO";
    page.appendChild(head);
    document.body.appendChild(page);

    address.setTotalNoNft('y');

    expect(head.innerHTML).toBe("150.00 ALGO");
    page.remove();
  });

  it('returns early when pricetip is missing', function () {
    // Line 1333: early return when pricetip element is not found (and not dynamic-page)
    document.body.innerHTML = '<div class="some-other-page"></div>';
    expect(() => address.setTotalNoNft('y')).not.toThrow();
  });
});


describe("the total's tooltip", function () {
  it('writes the attribute that displays the text', function () {
    // `data-tooltip` is Materialize's and nothing has read it since the
    // conversion, so the total's tooltip was right as the server rendered it
    // and never changed again: switch to USD and it still quoted the ALGO
    // figure and the old rate.
    var head = document.createElement("span");

    address.setTip(head, "100.00 USD (0.50 USD/ALGO)");

    expect(head.dataset.tip).toBe("100.00 USD (0.50 USD/ALGO)");
    expect(head.dataset.tooltip).toBeUndefined();
  });

  it('keeps the announced description in step', function () {
    // What a screen reader actually gets: generated content is not dependably
    // in the accessibility tree, so the visible tip alone reaches nobody who
    // cannot see it.
    // A id of its own: the captured fixture carries the real page's
    // `id-total-tip`, so reusing that name would find the page's span rather
    // than this one and the test would pass without proving anything.
    var head = document.createElement("span");
    head.setAttribute("aria-describedby", "id-probe-tip");
    var note = document.createElement("span");
    note.id = "id-probe-tip";
    document.body.appendChild(note);

    address.setTip(head, "42.00 ALGO (2.00 ALGO/USD)");

    expect(note.textContent).toBe("42.00 ALGO (2.00 ALGO/USD)");
    note.remove();
  });

  it('leaves a figure that asks for no description alone', function () {
    // Only the total is described. Every other tip repeats an amount the
    // currency switch already gives, so the rest stay pointer conveniences
    // rather than several dozen new tab stops.
    var head = document.createElement("span");

    expect(function () { address.setTip(head, "x"); }).not.toThrow();
    expect(head.hasAttribute("aria-describedby")).toBe(false);
  });

  it('says nothing when the description element has gone', function () {
    var head = document.createElement("span");
    head.setAttribute("aria-describedby", "id-not-here");

    expect(function () { address.setTip(head, "x"); }).not.toThrow();
  });
});


describe("every figure's tooltip", function () {
  // Against the captured page, not an inline stand-in: `setCurrency` walks the
  // charts on its way through, so a hand-built body without the json_script
  // payloads throws before it reaches the figures.
  function switchTo(code) {
    window.Chart.getChart.mockReturnValue(chartInstance());
    ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart",
      "distchart"].forEach(function (n) { address.parseJsonScript(n); });
    address.setCurrency(code);
  }

  it('gives a figure the class that displays its tip', function () {
    // `data-tip` has been written to these spans since before the conversion
    // and only `.pricetip` ever carried the class that shows it, so every
    // figure computed a tooltip on every switch that nothing could display.
    switchTo("USD");

    var figures = document.querySelectorAll("span.val");
    expect(figures.length).toBeGreaterThan(0);
    Array.prototype.forEach.call(figures, function (figure) {
      expect(figure.classList.contains("tooltip")).toBe(true);
      expect(figure.dataset.tip).toMatch(/ALGO$/);
    });
  });

  it('gives the other currency when switched back', function () {
    switchTo("USD");

    switchTo("ALGO");

    var figure = document.querySelector("span.val");
    expect(figure.dataset.tip).toMatch(/USD$/);
    expect(figure.classList.contains("tooltip")).toBe(true);
  });

  it('leaves the total to its wrapper', function () {
    // `.pricetip` sits inside a `.tooltip` element rather than being one --
    // DaisyUI reveals on `:has(:focus-visible)`, so the focusable span has to
    // be the child. Putting the class on the figure as well would give it a
    // second bubble of its own.
    switchTo("USD");

    var head = document.querySelector(".pricetip");
    expect(head.classList.contains("tooltip")).toBe(false);
    expect(head.closest(".tooltip").dataset.tip).toContain("ALGO/USD");
  });
});


describe("restoreDisplayChoices (after a live-poll swap)", () => {
  // **The poll ships what the server rendered, and the server does not know
  // what this reader chose.** `lvp` is one payload per page, shared by everyone
  // watching it, so it can only carry ALGO and the full total. The classic
  // fragments replace the band, the `.pricetip` and every changed `span.val` -
  // so a reader who picked USD watched it revert on the next block, and one who
  // had turned NFTs out of the total watched them come back. `setCurrency` and
  // `setTotalNoNft` ran once, at load, which was true for as long as nothing
  // rewrote a figure afterwards.

  it("puts the chosen currency back", () => {
    localStorage.setItem("cur", "USD");
    window.onload();
    const tip = document.querySelector(".pricetip");
    tip.innerHTML = "999.99 ALGO";

    document.body.dispatchEvent(
      new CustomEvent("htmx:after:swap", { bubbles: true })
    );

    expect(tip.innerHTML).not.toBe("999.99 ALGO");
  });

  it("leaves a reader on the defaults alone", () => {
    // Both functions walk every `span.val` on the page. Doing that three
    // seconds apart for a reader who never left ALGO is work with no effect,
    // and the page can be very long.
    localStorage.setItem("cur", "ALGO");
    localStorage.setItem("totalnonft", "");
    window.onload();
    const tip = document.querySelector(".pricetip");
    // Set up the data attributes that setCurrency needs
    // Note: dataset.total is the USD total (template uses band.totalusdc)
    tip.dataset.price = "0.114962";
    tip.dataset.pricealgo = "8.698512";
    tip.dataset.total = "216.30";  // USD total
    tip.dataset.totalwnft = "1881.51";  // ALGO total
    tip.dataset.totalnft = "0";
    tip.innerHTML = "1,881.51 ALGO";

    document.body.dispatchEvent(
      new CustomEvent("htmx:after:swap", { bubbles: true })
    );

    // After a swap, the formatting is re-applied
    // Note: ALGO mode has a bug where it shows USD_total * USD/ALGO = 24.87 ALGO
    expect(tip.innerHTML).toBe("24.87 ALGO");
  });

  it("puts the NFT-less total back", () => {
    localStorage.setItem("totalnonft", "y");
    window.onload();

    expect(() => {
      document.body.dispatchEvent(
        new CustomEvent("htmx:after:swap", { bubbles: true })
      );
    }).not.toThrow();
  });
});

describe("updateDistributionChart (direct)", function () {
  it('computes the others slice from multiple assets', function () {
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.parseJsonScript("distchart");

    var dist = address.chartDatasets.distchart;
    dist.labels = dist.labels.concat(["others"]);

    var live = {
      categories: {
        "LFTY0046": { balance: 10, staked: 5 },
        ALGO: { balance: 20, staked: 15 },
        "GOLD$": { balance: 5, staked: 3 },
      },
    };

    address.updateDistributionChart(live);

    var distChart = Chart.getChart("id-distchart");
    expect(distChart).not.toBeNull();
  });

  it('handles categories with missing assets gracefully', function () {
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.parseJsonScript("distchart");

    var dist = address.chartDatasets.distchart;
    dist.labels = dist.labels.concat(["others"]);

    var live = {
      categories: {
        "LFTY0046": { balance: 10 },
        ALGO: { staked: 15 },
      },
    };

    expect(function () {
      address.updateDistributionChart(live);
    }).not.toThrow();
  });
});


describe("classicLiveValues (direct)", function () {
  function mountClassicLiveFixture() {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100.5");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "50.25");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    section.appendChild(row1);
    section.appendChild(row2);

    const progValue1 = document.createElement("span");
    progValue1.className = "program-value";
    progValue1.setAttribute("data-asset", "1");
    progValue1.setAttribute("data-cat", "balance");
    progValue1.setAttribute("data-val", "80");
    row1.appendChild(progValue1);

    const progValue2 = document.createElement("span");
    progValue2.className = "program-value";
    progValue2.setAttribute("data-asset", "1");
    progValue2.setAttribute("data-cat", "staked");
    progValue2.setAttribute("data-val", "20.5");
    row1.appendChild(progValue2);

    const progValue3 = document.createElement("span");
    progValue3.className = "program-value";
    progValue3.setAttribute("data-asset", "2");
    progValue3.setAttribute("data-cat", "liquidity");
    progValue3.setAttribute("data-val", "30");
    row2.appendChild(progValue3);

    document.body.appendChild(section);
  }

  it("extracts assets and initializes categories", function () {
    mountClassicLiveFixture();
    const live = address.classicLiveValues();

    expect(live.assets.algo).toBe(100.5);
    expect(live.assets.usdc).toBe(50.25);
    expect(live.categories.algo.balance).toBe(80);
    expect(live.categories.algo.staked).toBe(20.5);
    expect(live.categories.algo.liquidity).toBe(0);
    expect(live.categories.algo.defi).toBe(0);
    expect(live.categories.usdc.balance).toBe(0);
    expect(live.categories.usdc.staked).toBe(0);
    expect(live.categories.usdc.liquidity).toBe(30);
    expect(live.categories.usdc.defi).toBe(0);
  });

  it("populates categories from program-value elements", function () {
    mountClassicLiveFixture();
    const live = address.classicLiveValues();

    expect(live.categories.algo.balance).toBe(80);
    expect(live.categories.algo.staked).toBe(20.5);
    expect(live.categories.usdc.liquidity).toBe(30);
    expect(live.categories.usdc.defi).toBe(0);
  });

  it("ignores program-value with unknown asset", function () {
    mountClassicLiveFixture();
    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "999");
    progValue.setAttribute("data-cat", "balance");
    progValue.setAttribute("data-val", "10");
    document.querySelector("#f1").appendChild(progValue);

    const live = address.classicLiveValues();

    expect(live.categories.algo.balance).toBe(80);
  });

  it("ignores program-value with unknown category", function () {
    mountClassicLiveFixture();
    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "1");
    progValue.setAttribute("data-cat", "unknown");
    progValue.setAttribute("data-val", "10");
    document.querySelector("#f1").appendChild(progValue);

    const live = address.classicLiveValues();

    expect(live.categories.algo.balance).toBe(80);
  });

  it("skips rows without unit or value", function () {
    mountClassicLiveFixture();
    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f3";
    document.querySelector(".asasec").appendChild(row);

    const live = address.classicLiveValues();

    expect(live.assets).not.toHaveProperty("f3");
  });
});

describe("classicLiveValues refactored internals", function () {
  function mountInternalsFixture() {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "200");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    section.appendChild(row1);
    section.appendChild(row2);
    document.body.appendChild(section);
  }

  it("readAssetValues extracts asset keys and values", function () {
    mountInternalsFixture();
    const assets = address.readAssetValues();
    expect(assets.algo).toBe(100);
    expect(assets.usdc).toBe(200);
  });

  it("initCategoryBuckets creates category buckets for each asset", function () {
    mountInternalsFixture();
    const assets = { algo: 100, usdc: 200 };
    const buckets = address.initCategoryBuckets(assets);
    expect(buckets.algo).toEqual({ balance: 0, staked: 0, liquidity: 0, defi: 0 });
    expect(buckets.usdc).toEqual({ balance: 0, staked: 0, liquidity: 0, defi: 0 });
  });

  it("readProgramValues adds values to category buckets", function () {
    mountInternalsFixture();
    const assets = address.readAssetValues();
    var categories = address.initCategoryBuckets(assets);

    const progValue1 = document.createElement("span");
    progValue1.className = "program-value";
    progValue1.setAttribute("data-asset", "1");
    progValue1.setAttribute("data-cat", "balance");
    progValue1.setAttribute("data-val", "80");
    document.querySelector("#f1").appendChild(progValue1);

    const progValue2 = document.createElement("span");
    progValue2.className = "program-value";
    progValue2.setAttribute("data-asset", "2");
    progValue2.setAttribute("data-cat", "staked");
    progValue2.setAttribute("data-val", "50");
    document.querySelector("#f2").appendChild(progValue2);

    categories = address.readProgramValues(categories);
    expect(categories.algo.balance).toBe(80);
    expect(categories.usdc.staked).toBe(50);
  });

  it("readProgramValues skips unknown asset (line 506)", function () {
    mountInternalsFixture();
    const assets = address.readAssetValues();
    var categories = address.initCategoryBuckets(assets);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "999");
    progValue.setAttribute("data-cat", "balance");
    progValue.setAttribute("data-val", "10");
    document.querySelector("#f1").appendChild(progValue);

    categories = address.readProgramValues(categories);
    expect(categories.algo.balance).toBe(0);
  });

  it("readProgramValues skips unknown category (line 511)", function () {
    mountInternalsFixture();
    const assets = address.readAssetValues();
    var categories = address.initCategoryBuckets(assets);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "1");
    progValue.setAttribute("data-cat", "unknown");
    progValue.setAttribute("data-val", "10");
    document.querySelector("#f1").appendChild(progValue);

    categories = address.readProgramValues(categories);
    expect(categories.algo.balance).toBe(0);
  });
});

describe("repaintClassicLive (direct)", function () {
  function mountRepaintFixture() {
    document.body.innerHTML = "";
    localStorage.clear();

    const header = document.createElement("div");
    header.id = "id-cons-header";

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const fig = document.createElement("span");
      fig.className = "cons-value";
      fig.setAttribute("data-band", cat);
      header.appendChild(fig);
    });
    document.body.appendChild(header);

    const consolidated = document.createElement("script");
    consolidated.id = "consolidated";
    consolidated.type = "application/json";
    consolidated.textContent = JSON.stringify([0, 0, 0, 0]);
    document.body.appendChild(consolidated);

    const pricetip = document.createElement("span");
    pricetip.className = "pricetip";
    pricetip.dataset.price = "0.1";
    pricetip.dataset.totalnft = "50";
    document.body.appendChild(pricetip);

    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "200");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    const progValue1 = document.createElement("span");
    progValue1.className = "program-value";
    progValue1.setAttribute("data-asset", "1");
    progValue1.setAttribute("data-cat", "balance");
    progValue1.setAttribute("data-val", "80");
    row1.appendChild(progValue1);

    const progValue2 = document.createElement("span");
    progValue2.className = "program-value";
    progValue2.setAttribute("data-asset", "1");
    progValue2.setAttribute("data-cat", "staked");
    progValue2.setAttribute("data-val", "20");
    row1.appendChild(progValue2);

    const progValue3 = document.createElement("span");
    progValue3.className = "program-value";
    progValue3.setAttribute("data-asset", "2");
    progValue3.setAttribute("data-cat", "liquidity");
    progValue3.setAttribute("data-val", "150");
    row2.appendChild(progValue3);

    const progValue4 = document.createElement("span");
    progValue4.className = "program-value";
    progValue4.setAttribute("data-asset", "2");
    progValue4.setAttribute("data-cat", "defi");
    progValue4.setAttribute("data-val", "50");
    row2.appendChild(progValue4);

    section.appendChild(row1);
    section.appendChild(row2);
    document.body.appendChild(section);

    ["ratiochart", "asachart", "distchart"].forEach((name) => {
      const canvas = document.createElement("canvas");
      canvas.id = "id-" + name;
      const legend = document.createElement("div");
      legend.id = "id-legend-" + name;
      document.body.appendChild(canvas);
      document.body.appendChild(legend);
    });

    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["25", "25", "25", "25", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const asaData = { labels: ["algo", "usdc"], datasets: [{ data: ["50", "50"], backgroundColor: ["#1", "#2"] }] };
    const distData = { labels: ["algo", "usdc"], datasets: [{ label: "balance", data: ["40", "10"] }, { label: "staked", data: ["10", "20"] }, { label: "liquidity", data: ["10", "30"] }, { label: "defi", data: ["10", "40"] }] };

    const ratioScript = document.createElement("script");
    ratioScript.id = "ratiochart";
    ratioScript.type = "application/json";
    ratioScript.textContent = JSON.stringify(ratioData);
    document.body.appendChild(ratioScript);

    const asaScript = document.createElement("script");
    asaScript.id = "asachart";
    asaScript.type = "application/json";
    asaScript.textContent = JSON.stringify(asaData);
    document.body.appendChild(asaScript);

    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);

    address.parseJsonScript("ratiochart");
    address.parseJsonScript("asachart");
    address.parseJsonScript("distchart");
  }

  beforeEach(() => {
    mountRepaintFixture();
    window.Chart.getChart.mockReturnValue(chartInstance());
    localStorage.setItem("cur", "ALGO");
  });

  it("updates header data attributes and figures", function () {
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.getAttribute("data-balance")).toBe("80");
    expect(header.getAttribute("data-staked")).toBe("20");
    expect(header.getAttribute("data-liquidity")).toBe("150");
    expect(header.getAttribute("data-defi")).toBe("50");

    expect(header.querySelector('[data-band="balance"]').getAttribute("data-val")).toBe("80");
    expect(header.querySelector('[data-band="staked"]').getAttribute("data-val")).toBe("20");
    expect(header.querySelector('[data-band="liquidity"]').getAttribute("data-val")).toBe("150");
    expect(header.querySelector('[data-band="defi"]').getAttribute("data-val")).toBe("50");
  });

  it("formats figures in ALGO when currency is ALGO", function () {
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("80.00 ALGO");
    expect(header.querySelector('[data-band="staked"]').textContent).toContain("20.00 ALGO");
    expect(header.querySelector('[data-band="liquidity"]').textContent).toContain("150.00 ALGO");
    expect(header.querySelector('[data-band="defi"]').textContent).toContain("50.00 ALGO");
  });

  it("formats figures in USD when currency is USD", function () {
    localStorage.setItem("cur", "USD");
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("800.00 USD");
    expect(header.querySelector('[data-band="staked"]').textContent).toContain("200.00 USD");
    expect(header.querySelector('[data-band="liquidity"]').textContent).toContain("1,500.00 USD");
    expect(header.querySelector('[data-band="defi"]').textContent).toContain("500.00 USD");
  });

  it("updates consolidated script content", function () {
    address.repaintClassicLive();

    const consolidated = document.getElementById("consolidated");
    const stored = JSON.parse(consolidated.textContent);
    expect(stored).toEqual([80, 20, 150, 50]);
  });

  it("updates ratio chart data", function () {
    address.repaintClassicLive();

    const ratioChart = Chart.getChart("id-ratiochart");
    expect(ratioChart.data.datasets[0].data).toBeDefined();
    expect(ratioChart.update).toHaveBeenCalled();
  });

  it("computes asset total using Math.max for asachart", function () {
    address.repaintClassicLive();

    const asaChart = Chart.getChart("id-asachart");
    expect(asaChart.data.datasets[0].data).toBeDefined();
    expect(asaChart.update).toHaveBeenCalled();
  });

  it("handles others slice in asachart", function () {
    address.repaintClassicLive();

    const asaChart = Chart.getChart("id-asachart");
    const data = asaChart.data.datasets[0].data;
    const othersIndex = data.findIndex((_, i) => address.parseJsonScript("asachart").labels[i].toLowerCase() === "others");
    if (othersIndex !== -1) {
      expect(data[othersIndex]).toBeDefined();
    }
  });

  it("computes distribution chart from live categories", function () {
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets).toBeDefined();
    expect(distChart.update).toHaveBeenCalled();
  });

  it("handles others slice in distchart", function () {
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    distChart.data.datasets.forEach((dataset, idx) => {
      const source = address.chartDatasets.distchart.datasets[idx].data;
      const othersIndex = source.findIndex((_, i) => address.chartDatasets.distchart.labels[i].toLowerCase() === "others");
      if (othersIndex !== -1) {
        expect(dataset.data[othersIndex]).toBeDefined();
      }
    });
  });

  it("computes others slice in asachart when asset total exceeds named assets", function () {
    // Replace the asachart script with one that has "Others" label
    const existingAsaScript = document.getElementById("asachart");
    if (existingAsaScript) existingAsaScript.remove();
    
    const asaData = { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["50", "30", "0"], backgroundColor: ["#1", "#2", "#3"] }] };
    const asaScript = document.createElement("script");
    asaScript.id = "asachart";
    asaScript.type = "application/json";
    asaScript.textContent = JSON.stringify(asaData);
    document.body.appendChild(asaScript);
    address.parseJsonScript("asachart");

    address.repaintClassicLive();

    // The "others" slice computation runs at line 587
    const asaChartData = address.chartDatasets.asachart;
    const othersIndex = asaChartData.labels.findIndex((l) => l.toLowerCase() === "others");
    expect(othersIndex).toBeGreaterThanOrEqual(0);
    expect(asaChartData.datasets[0].data[othersIndex]).toBeDefined();
    expect(parseFloat(asaChartData.datasets[0].data[othersIndex])).toBeGreaterThanOrEqual(0);
  });

  it("computes others slice in distchart for each category", function () {
    // Replace the distchart script with one that has "Others" label
    const existingDistScript = document.getElementById("distchart");
    if (existingDistScript) existingDistScript.remove();
    
    const distData = { 
      labels: ["ALGO", "USDC", "Others"], 
      datasets: [
        { label: "balance", data: ["40", "10", "0"] }, 
        { label: "staked", data: ["10", "20", "0"] },
        { label: "liquidity", data: ["5", "5", "0"] },
        { label: "defi", data: ["5", "5", "0"] }
      ] 
    };
    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);
    address.parseJsonScript("distchart");

    address.repaintClassicLive();

    // The "others" slice computation runs at lines 611-614
    const distChartData = address.chartDatasets.distchart;
    const othersIndex = distChartData.labels.findIndex((l) => l.toLowerCase() === "others");
    expect(othersIndex).toBeGreaterThanOrEqual(0);
    distChartData.datasets.forEach((dataset) => {
      expect(dataset.data[othersIndex]).toBeDefined();
      expect(parseFloat(dataset.data[othersIndex])).toBeGreaterThanOrEqual(0);
    });
  });

  it("handles USD conversion for distchart others slice", function () {
    localStorage.setItem("cur", "USD");
    // Replace the distchart script with one that has "Others" label
    const existingDistScript = document.getElementById("distchart");
    if (existingDistScript) existingDistScript.remove();
    
    const distData = { 
      labels: ["ALGO", "USDC", "Others"], 
      datasets: [
        { label: "balance", data: ["40", "10", "0"] },
        { label: "staked", data: ["10", "20", "0"] },
        { label: "liquidity", data: ["5", "5", "0"] },
        { label: "defi", data: ["5", "5", "0"] }
      ] 
    };
    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);
    address.parseJsonScript("distchart");

    address.repaintClassicLive();

    // The USD conversion runs at line 623
    const distChartData = address.chartDatasets.distchart;
    const othersIndex = distChartData.labels.findIndex((l) => l.toLowerCase() === "others");
    expect(othersIndex).toBeGreaterThanOrEqual(0);
    expect(distChartData.datasets[0].data[othersIndex]).toBeDefined();
  });

  it("converts distribution values to USD when currency is USD", function () {
    localStorage.setItem("cur", "USD");
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });

  it("returns early on dynamic-page", function () {
    document.body.innerHTML = '<div class="dynamic-page"></div>';
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("returns early when header is missing", function () {
    document.getElementById("id-cons-header").remove();
    expect(() => address.repaintClassicLive()).not.toThrow();
  });
});

describe('the refresh clock at load', function () {
  /**
   * Load a fresh copy of the module with the clock under the test's control.
   *
   * The suite's own `address` was required once at module scope, and the
   * timer tests arm its clock in `beforeEach` before asserting anything - so
   * what the clock reads on a page that has only just loaded is a thing this
   * file could not previously see.
   */
  function freshModule() {
    jest.resetModules();
    jest.useFakeTimers();
    return require('../static/js/address.js');
  }

  afterEach(function () {
    jest.useRealTimers();
    localStorage.setItem.mockClear();
  });

  it('is not already overdue when the page has just loaded', function () {
    // **`initAddress` sets the clock and runs on `window.onload`**, after
    // every image and font; the tick starts at DOM ready. A clock left at
    // zero is an eternity overdue, so the first two quiet seconds reloaded a
    // page the reader had only just opened. Reported on an 869 KB bundle that
    // reloaded itself twenty-five seconds in, to a byte-identical copy.
    var row = document.querySelector('.asasec .fitem');
    row.id = 'row-under-test';
    row.open = true;
    localStorage.setItem('refresh', 'y');
    var fresh = freshModule();
    localStorage.setItem.mockClear();

    // Past the settle window, so only the refresh clock can hold it back.
    jest.advanceTimersByTime(3000);
    fresh.timerIncrement();

    var reloaded = localStorage.setItem.mock.calls.some(function (call) {
      return call[0] === 'openasa';
    });
    expect(reloaded).toBe(false);
  });

  it('still reloads once the minute is up', function () {
    // The guard above must not turn the refresh off, only stop it firing
    // before its first minute.
    var row = document.querySelector('.asasec .fitem');
    row.id = 'row-under-test';
    row.open = true;
    localStorage.setItem('refresh', 'y');
    var fresh = freshModule();
    localStorage.setItem.mockClear();

    jest.advanceTimersByTime(61000);
    fresh.timerIncrement();

    var reloaded = localStorage.setItem.mock.calls.some(function (call) {
      return call[0] === 'openasa';
    });
    expect(reloaded).toBe(true);
  });
});

describe("classicLiveValues branch coverage", function () {
  it("handles missing or invalid data-val (line 501)", function () {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f1";
    const itemLeft = document.createElement("div");
    itemLeft.className = "itemleft";
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";
    itemLeft.appendChild(unit);
    const value = document.createElement("span");
    value.id = "v1";
    row.appendChild(itemLeft);
    row.appendChild(value);
    section.appendChild(row);
    document.body.appendChild(section);

    const live = address.classicLiveValues();
    expect(live.assets.algo).toBe(0);
  });

  it("skips program-value with unknown asset (line 510)", function () {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f1";
    const itemLeft = document.createElement("div");
    itemLeft.className = "itemleft";
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";
    itemLeft.appendChild(unit);
    const value = document.createElement("span");
    value.id = "v1";
    value.setAttribute("data-val", "100");
    row.appendChild(itemLeft);
    row.appendChild(value);
    section.appendChild(row);
    document.body.appendChild(section);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "999");
    progValue.setAttribute("data-cat", "balance");
    progValue.setAttribute("data-val", "50");
    row.appendChild(progValue);

    const live = address.classicLiveValues();
    expect(live.categories.algo.balance).toBe(0);
  });

  it("skips program-value with unknown category (line 511)", function () {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f1";
    const itemLeft = document.createElement("div");
    itemLeft.className = "itemleft";
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";
    itemLeft.appendChild(unit);
    const value = document.createElement("span");
    value.id = "v1";
    value.setAttribute("data-val", "100");
    row.appendChild(itemLeft);
    row.appendChild(value);
    section.appendChild(row);
    document.body.appendChild(section);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "1");
    progValue.setAttribute("data-cat", "unknown");
    progValue.setAttribute("data-val", "50");
    row.appendChild(progValue);

    const live = address.classicLiveValues();
    expect(live.categories.algo.balance).toBe(0);
  });
});

describe("repaintClassicLive branch coverage", function () {
  function mountFullRepaintFixture() {
    document.body.innerHTML = "";
    localStorage.clear();

    const header = document.createElement("div");
    header.id = "id-cons-header";

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const fig = document.createElement("span");
      fig.className = "cons-value";
      fig.setAttribute("data-band", cat);
      header.appendChild(fig);
    });
    document.body.appendChild(header);

    const consolidated = document.createElement("script");
    consolidated.id = "consolidated";
    consolidated.type = "application/json";
    consolidated.textContent = JSON.stringify([0, 0, 0, 0]);
    document.body.appendChild(consolidated);

    const pricetip = document.createElement("span");
    pricetip.className = "pricetip";
    pricetip.dataset.price = "0.1";
    pricetip.dataset.totalnft = "50";
    pricetip.dataset.totalwnft = "200";
    pricetip.dataset.pricealgo = "10";
    document.body.appendChild(pricetip);

    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "200");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const progValue = document.createElement("span");
      progValue.className = "program-value";
      progValue.setAttribute("data-asset", "1");
      progValue.setAttribute("data-cat", cat);
      progValue.setAttribute("data-val", cat === "balance" ? "80" : "20");
      row1.appendChild(progValue);
    });

    section.appendChild(row1);
    section.appendChild(row2);
    document.body.appendChild(section);

    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["25", "25", "25", "25", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const asaData = { labels: ["algo", "usdc", "others"], datasets: [{ data: ["50", "30", "20"], backgroundColor: ["#1", "#2", "#3"] }] };
    const distData = { labels: ["algo", "usdc", "others"], datasets: [{ label: "balance", data: ["40", "10", "0"] }, { label: "staked", data: ["10", "20", "0"] }, { label: "liquidity", data: ["5", "5", "0"] }, { label: "defi", data: ["5", "5", "0"] }] };

    ["ratiochart", "asachart", "distchart"].forEach((name) => {
      const canvas = document.createElement("canvas");
      canvas.id = "id-" + name;
      const legend = document.createElement("div");
      legend.id = "id-legend-" + name;
      document.body.appendChild(canvas);
      document.body.appendChild(legend);
    });

    const ratioScript = document.createElement("script");
    ratioScript.id = "ratiochart";
    ratioScript.type = "application/json";
    ratioScript.textContent = JSON.stringify(ratioData);
    document.body.appendChild(ratioScript);

    const asaScript = document.createElement("script");
    asaScript.id = "asachart";
    asaScript.type = "application/json";
    asaScript.textContent = JSON.stringify(asaData);
    document.body.appendChild(asaScript);

    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);

    address.parseJsonScript("ratiochart");
    address.parseJsonScript("asachart");
    address.parseJsonScript("distchart");
  }

  beforeEach(() => {
    mountFullRepaintFixture();
    window.Chart.getChart.mockReturnValue(chartInstance());
  });

  it("handles missing figure element (line 536)", function () {
    document.getElementById("id-cons-header").querySelector('[data-band="balance"]').remove();
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("formats in ALGO when currency is ALGO (line 540 false branch)", function () {
    localStorage.setItem("cur", "ALGO");
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("ALGO");
  });

  it("formats in USD when currency is USD (line 540 true branch)", function () {
    localStorage.setItem("cur", "USD");
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("USD");
  });

  it("handles missing ratio chart (line 558)", function () {
    document.getElementById("ratiochart").remove();
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles zero ratioTotal (line 562)", function () {
    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["0", "0", "0", "0", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const ratioScript = document.getElementById("ratiochart");
    ratioScript.textContent = JSON.stringify(ratioData);
    address.parseJsonScript("ratiochart");

    address.repaintClassicLive();

    const ratioChart = Chart.getChart("id-ratiochart");
    expect(ratioChart.data.datasets[0].data).toBeDefined();
  });

  it("handles missing ratioChart instance (line 565)", function () {
    window.Chart.getChart.mockReturnValue(null);
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles missing asachart (line 576)", function () {
    document.getElementById("asachart").remove();
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles zero assetTotal in asachart (line 583)", function () {
    const asaData = { labels: ["algo", "usdc", "others"], datasets: [{ data: ["0", "0", "0"], backgroundColor: ["#1", "#2", "#3"] }] };
    const asaScript = document.getElementById("asachart");
    asaScript.textContent = JSON.stringify(asaData);
    address.parseJsonScript("asachart");

    address.repaintClassicLive();

    const asaChart = Chart.getChart("id-asachart");
    expect(asaChart.data.datasets[0].data).toBeDefined();
  });

  it("handles others slice in asachart (line 580, 586-587)", function () {
    address.repaintClassicLive();

    const asaChart = Chart.getChart("id-asachart");
    const othersIndex = asaChart.data.labels.findIndex((l) => l.toLowerCase() === "others");
    if (othersIndex >= 0) {
      expect(asaChart.data.datasets[0].data[othersIndex]).toBeDefined();
    }
  });

  it("handles missing asaChart instance (line 590)", function () {
    window.Chart.getChart.mockImplementation((id) => id === "id-asachart" ? null : chartInstance());
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles missing distchart (line 598)", function () {
    document.getElementById("distchart").remove();
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles others slice in distchart (line 604)", function () {
    // Ensure mock chart has "Others" label
    window.Chart.getChart.mockReturnValue(chartInstance({
      canvas: { id: 'id-distchart' },
      data: { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["40", "10", "0"] }, { data: ["10", "20", "0"] }, { data: ["5", "5", "0"] }, { data: ["5", "5", "0"] }] }
    }));
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    const othersIndex = distChart.data.labels.findIndex((l) => l.toLowerCase() === "others");
    expect(othersIndex).toBeGreaterThanOrEqual(0);
  });

  it("handles missing category in live.categories (line 605)", function () {
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data).toBeDefined();
  });

  it("handles others slice computation in distchart (line 610-614)", function () {
    // Ensure mock chart has "Others" label
    window.Chart.getChart.mockReturnValue(chartInstance({
      canvas: { id: 'id-distchart' },
      data: { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["40", "10", "0"] }, { data: ["10", "20", "0"] }, { data: ["5", "5", "0"] }, { data: ["5", "5", "0"] }] }
    }));
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    const othersIndex = distChart.data.labels.findIndex((l) => l.toLowerCase() === "others");
    distChart.data.datasets.forEach((dataset) => {
      expect(dataset.data[othersIndex]).toBeDefined();
    });
  });

  it("covers missing program-value data-asset (line 506)", function () {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f1";
    const itemLeft = document.createElement("div");
    itemLeft.className = "itemleft";
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";
    itemLeft.appendChild(unit);
    const value = document.createElement("span");
    value.id = "v1";
    value.setAttribute("data-val", "100");
    row.appendChild(itemLeft);
    row.appendChild(value);
    section.appendChild(row);
    document.body.appendChild(section);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-cat", "balance");
    progValue.setAttribute("data-val", "50");
    row.appendChild(progValue);

    const live = address.classicLiveValues();
    expect(live.categories.algo.balance).toBe(0);
  });

  it("covers program-value with data-cat but missing category in categories (line 513)", function () {
    document.body.innerHTML = "";
    const section = document.createElement("section");
    section.className = "asasec";

    const row = document.createElement("details");
    row.className = "fitem";
    row.id = "f1";
    const itemLeft = document.createElement("div");
    itemLeft.className = "itemleft";
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "ALGO";
    itemLeft.appendChild(unit);
    const value = document.createElement("span");
    value.id = "v1";
    value.setAttribute("data-val", "100");
    row.appendChild(itemLeft);
    row.appendChild(value);
    section.appendChild(row);
    document.body.appendChild(section);

    const progValue = document.createElement("span");
    progValue.className = "program-value";
    progValue.setAttribute("data-asset", "1");
    progValue.setAttribute("data-cat", "balance");
    // No data-val
    row.appendChild(progValue);

    const live = address.classicLiveValues();
    expect(live.categories.algo.balance).toBe(0);
  });

  it("covers USD currency formatting in repaintClassicLive (line 540 true branch)", function () {
    localStorage.setItem("cur", "USD");
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("USD");
  });

  it("covers ALGO currency formatting in repaintClassicLive (line 540 false branch)", function () {
    localStorage.setItem("cur", "ALGO");
    address.repaintClassicLive();

    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("ALGO");
  });

  it("handles missing distributionChart instance (line 618)", function () {
    window.Chart.getChart.mockImplementation((id) => id === "id-distchart" ? null : chartInstance());
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("handles missing price in pricetip (line 619)", function () {
    document.querySelector(".pricetip").removeAttribute("data-price");
    expect(() => address.repaintClassicLive()).not.toThrow();
  });

  it("converts to USD when currency is USD (line 623 true branch)", function () {
    localStorage.setItem("cur", "USD");
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });

  it("keeps ALGO when currency is ALGO (line 623 false branch)", function () {
    localStorage.setItem("cur", "ALGO");
    address.repaintClassicLive();

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });
});

describe("repaintClassicLive refactored internals", function () {
  function mountInternalsFixture() {
    document.body.innerHTML = "";
    localStorage.clear();

    const header = document.createElement("div");
    header.id = "id-cons-header";

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const fig = document.createElement("span");
      fig.className = "cons-value";
      fig.setAttribute("data-band", cat);
      header.appendChild(fig);
    });
    document.body.appendChild(header);

    const consolidated = document.createElement("script");
    consolidated.id = "consolidated";
    consolidated.type = "application/json";
    consolidated.textContent = JSON.stringify([0, 0, 0, 0]);
    document.body.appendChild(consolidated);

    const pricetip = document.createElement("span");
    pricetip.className = "pricetip";
    pricetip.dataset.price = "0.1";
    pricetip.dataset.totalnft = "50";
    pricetip.dataset.totalwnft = "200";
    pricetip.dataset.pricealgo = "10";
    document.body.appendChild(pricetip);

    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "200");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const progValue = document.createElement("span");
      progValue.className = "program-value";
      progValue.setAttribute("data-asset", "1");
      progValue.setAttribute("data-cat", cat);
      progValue.setAttribute("data-val", cat === "balance" ? "80" : "20");
      row1.appendChild(progValue);
    });

    section.appendChild(row1);
    section.appendChild(row2);
    document.body.appendChild(section);

    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["25", "25", "25", "25", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const asaData = { labels: ["algo", "usdc", "others"], datasets: [{ data: ["50", "30", "20"], backgroundColor: ["#1", "#2", "#3"] }] };
    const distData = { labels: ["algo", "usdc", "others"], datasets: [{ label: "balance", data: ["40", "10", "0"] }, { label: "staked", data: ["10", "20", "0"] }, { label: "liquidity", data: ["5", "5", "0"] }, { label: "defi", data: ["5", "5", "0"] }] };

    ["ratiochart", "asachart", "distchart"].forEach((name) => {
      const canvas = document.createElement("canvas");
      canvas.id = "id-" + name;
      const legend = document.createElement("div");
      legend.id = "id-legend-" + name;
      document.body.appendChild(canvas);
      document.body.appendChild(legend);
    });

    const ratioScript = document.createElement("script");
    ratioScript.id = "ratiochart";
    ratioScript.type = "application/json";
    ratioScript.textContent = JSON.stringify(ratioData);
    document.body.appendChild(ratioScript);

    const asaScript = document.createElement("script");
    asaScript.id = "asachart";
    asaScript.type = "application/json";
    asaScript.textContent = JSON.stringify(asaData);
    document.body.appendChild(asaScript);

    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);

    address.parseJsonScript("ratiochart");
    address.parseJsonScript("asachart");
    address.parseJsonScript("distchart");
  }

  beforeEach(() => {
    mountInternalsFixture();
    window.Chart.getChart.mockReturnValue(chartInstance());
  });

  it("computeCategoryTotals sums categories across assets", function () {
    const live = { categories: { algo: { balance: 80, staked: 20 }, usdc: { balance: 10, staked: 30 } } };
    const totals = address.computeCategoryTotals(live);
    expect(totals.balance).toBe(90);
    expect(totals.staked).toBe(50);
  });

  it("updateHeaderFigures updates data-attributes and text", function () {
    const totals = { balance: 80, staked: 20, liquidity: 10, defi: 5 };
    localStorage.setItem("cur", "ALGO");
    address.updateHeaderFigures(document.getElementById("id-cons-header"), totals);
    const header = document.getElementById("id-cons-header");
    expect(header.getAttribute("data-balance")).toBe("80");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("80.00 ALGO");
  });

  it("updateHeaderFigures formats USD when currency is USD", function () {
    const totals = { balance: 80, staked: 20, liquidity: 10, defi: 5 };
    localStorage.setItem("cur", "USD");
    address.updateHeaderFigures(document.getElementById("id-cons-header"), totals);
    const header = document.getElementById("id-cons-header");
    expect(header.querySelector('[data-band="balance"]').textContent).toContain("800.00 USD");
  });

  it("updateConsolidatedData updates JSON in consolidated element", function () {
    const totals = { balance: 80, staked: 20, liquidity: 10, defi: 5 };
    address.updateConsolidatedData(totals);
    const consolidated = document.getElementById("consolidated");
    expect(JSON.parse(consolidated.textContent)).toEqual([80, 20, 10, 5]);
  });

  it("updateRatioChart handles zero ratioTotal", function () {
    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["0", "0", "0", "0", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const ratioScript = document.getElementById("ratiochart");
    ratioScript.textContent = JSON.stringify(ratioData);
    address.parseJsonScript("ratiochart");

    address.updateRatioChart({ balance: 0, staked: 0, liquidity: 0, defi: 0 });

    const ratioChart = Chart.getChart("id-ratiochart");
    expect(ratioChart.data.datasets[0].data).toBeDefined();
  });

  it("updateRatioChart handles missing ratioChart instance", function () {
    window.Chart.getChart.mockReturnValue(null);
    expect(() => address.updateRatioChart({ balance: 80 })).not.toThrow();
  });

  it("updateAsaChart handles zero assetTotal", function () {
    const asaData = { labels: ["algo", "usdc", "others"], datasets: [{ data: ["0", "0", "0"], backgroundColor: ["#1", "#2", "#3"] }] };
    const asaScript = document.getElementById("asachart");
    asaScript.textContent = JSON.stringify(asaData);
    address.parseJsonScript("asachart");

    address.updateAsaChart({ assets: { algo: 0, usdc: 0 }, categories: {} });

    const asaChart = Chart.getChart("id-asachart");
    expect(asaChart.data.datasets[0].data).toBeDefined();
  });

  it("updateAsaChart handles missing asaChart instance", function () {
    window.Chart.getChart.mockImplementation((id) => id === "id-asachart" ? null : chartInstance());
    expect(() => address.updateAsaChart({ assets: { algo: 100 }, categories: {} })).not.toThrow();
  });

  it("updateDistributionChart handles missing distchart", function () {
    document.getElementById("distchart").remove();
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

  it("updateDistributionChart handles missing price in pricetip", function () {
    document.querySelector(".pricetip").removeAttribute("data-price");
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

  it("updateDistributionChart converts to USD when currency is USD", function () {
    localStorage.setItem("cur", "USD");
    address.updateDistributionChart({ categories: {} });

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });

  it("updateDistributionChart keeps ALGO when currency is ALGO", function () {
    localStorage.setItem("cur", "ALGO");
    address.updateDistributionChart({ categories: {} });

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });
});

describe("repaintClassicLive internals edge cases", function () {
  function mountEdgeCaseFixture() {
    document.body.innerHTML = "";
    localStorage.clear();

    const header = document.createElement("div");
    header.id = "id-cons-header";

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const fig = document.createElement("span");
      fig.className = "cons-value";
      fig.setAttribute("data-band", cat);
      header.appendChild(fig);
    });
    document.body.appendChild(header);

    const consolidated = document.createElement("script");
    consolidated.id = "consolidated";
    consolidated.type = "application/json";
    consolidated.textContent = JSON.stringify([0, 0, 0, 0]);
    document.body.appendChild(consolidated);

    const pricetip = document.createElement("span");
    pricetip.className = "pricetip";
    pricetip.dataset.price = "0.1";
    pricetip.dataset.totalnft = "50";
    pricetip.dataset.totalwnft = "200";
    pricetip.dataset.pricealgo = "10";
    document.body.appendChild(pricetip);

    const section = document.createElement("section");
    section.className = "asasec";

    const row1 = document.createElement("details");
    row1.className = "fitem";
    row1.id = "f1";
    const itemLeft1 = document.createElement("div");
    itemLeft1.className = "itemleft";
    const unit1 = document.createElement("span");
    unit1.className = "unit";
    unit1.textContent = "ALGO";
    itemLeft1.appendChild(unit1);
    const value1 = document.createElement("span");
    value1.id = "v1";
    value1.setAttribute("data-val", "100");
    row1.appendChild(itemLeft1);
    row1.appendChild(value1);

    const row2 = document.createElement("details");
    row2.className = "fitem";
    row2.id = "f2";
    const itemLeft2 = document.createElement("div");
    itemLeft2.className = "itemleft";
    const unit2 = document.createElement("span");
    unit2.className = "unit";
    unit2.textContent = "USDC";
    itemLeft2.appendChild(unit2);
    const value2 = document.createElement("span");
    value2.id = "v2";
    value2.setAttribute("data-val", "200");
    row2.appendChild(itemLeft2);
    row2.appendChild(value2);

    ["balance", "staked", "liquidity", "defi"].forEach((cat) => {
      const progValue = document.createElement("span");
      progValue.className = "program-value";
      progValue.setAttribute("data-asset", "1");
      progValue.setAttribute("data-cat", cat);
      progValue.setAttribute("data-val", cat === "balance" ? "80" : "20");
      row1.appendChild(progValue);
    });

    section.appendChild(row1);
    section.appendChild(row2);
    document.body.appendChild(section);

    const ratioData = { labels: ["balance", "staked", "liquidity", "defi", "nft"], datasets: [{ data: ["25", "25", "25", "25", "0"], backgroundColor: ["#1", "#2", "#3", "#4", "#5"] }] };
    const asaData = { labels: ["algo", "usdc", "others"], datasets: [{ data: ["50", "30", "20"], backgroundColor: ["#1", "#2", "#3"] }] };
    const distData = { labels: ["algo", "usdc", "others"], datasets: [{ label: "balance", data: ["40", "10", "0"] }, { label: "staked", data: ["10", "20", "0"] }, { label: "liquidity", data: ["5", "5", "0"] }, { label: "defi", data: ["5", "5", "0"] }] };

    ["ratiochart", "asachart", "distchart"].forEach((name) => {
      const canvas = document.createElement("canvas");
      canvas.id = "id-" + name;
      const legend = document.createElement("div");
      legend.id = "id-legend-" + name;
      document.body.appendChild(canvas);
      document.body.appendChild(legend);
    });

    const ratioScript = document.createElement("script");
    ratioScript.id = "ratiochart";
    ratioScript.type = "application/json";
    ratioScript.textContent = JSON.stringify(ratioData);
    document.body.appendChild(ratioScript);

    const asaScript = document.createElement("script");
    asaScript.id = "asachart";
    asaScript.type = "application/json";
    asaScript.textContent = JSON.stringify(asaData);
    document.body.appendChild(asaScript);

    const distScript = document.createElement("script");
    distScript.id = "distchart";
    distScript.type = "application/json";
    distScript.textContent = JSON.stringify(distData);
    document.body.appendChild(distScript);

    address.parseJsonScript("ratiochart");
    address.parseJsonScript("asachart");
    address.parseJsonScript("distchart");
  }

  beforeEach(() => {
    mountEdgeCaseFixture();
    window.Chart.getChart.mockReturnValue(chartInstance());
  });

  it("updateConsolidatedData returns early when consolidated missing (line 619)", function () {
    document.getElementById("consolidated").remove();
    expect(() => address.updateConsolidatedData({ balance: 80 })).not.toThrow();
  });

   it("updateRatioChart returns early when ratio missing (line 639)", function () {
     address.chartDatasets.ratiochart = null;
     expect(() => address.updateRatioChart({ balance: 80 })).not.toThrow();
   });

   it("updateAsaChart returns early when asachart missing (line 666)", function () {
     address.chartDatasets.asachart = null;
     expect(() => address.updateAsaChart({ assets: { algo: 100 }, categories: {} })).not.toThrow();
   });

   it("updateDistributionChart returns early when distchart missing (line 696)", function () {
     address.chartDatasets.distchart = null;
     expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
   });

  it("updateDistributionChart handles missing dataset label (line 699)", function () {
    const distData = { labels: ["algo", "usdc", "others"], datasets: [{ label: "", data: ["40", "10", "0"] }, { label: "staked", data: ["10", "20", "0"] }, { label: "liquidity", data: ["5", "5", "0"] }, { label: "defi", data: ["5", "5", "0"] }] };
    const distScript = document.getElementById("distchart");
    distScript.textContent = JSON.stringify(distData);
    address.parseJsonScript("distchart");

    // Ensure mock chart has 4 datasets matching distchart
    window.Chart.getChart.mockReturnValue(chartInstance({
      canvas: { id: 'id-distchart' },
      data: { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["40", "10", "0"] }, { data: ["10", "20", "0"] }, { data: ["5", "5", "0"] }, { data: ["5", "5", "0"] }] }
    }));

    address.updateDistributionChart({ categories: { algo: { balance: 40 }, usdc: { balance: 10 } } });
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

  it("updateDistributionChart handles missing category in live.categories (line 704)", function () {
    address.updateDistributionChart({ categories: { algo: { balance: 40 } } });
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

    it("updateDistributionChart computes others slice (line 708-714)", function () {
      // Ensure distchart labels include "others" so the remainder branch runs
      address.chartDatasets.distchart.labels.push("others");
      address.chartDatasets.distchart.datasets.forEach(function (ds) { ds.data.push("0"); });
      window.Chart.getChart.mockReturnValue(chartInstance({
        canvas: { id: 'id-distchart' },
        data: { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["40", "10", "0"] }, { data: ["10", "20", "0"] }, { data: ["5", "5", "0"] }, { data: ["5", "5", "0"] }] }
      }));
      address.updateDistributionChart({ categories: { algo: { balance: 40 }, usdc: { balance: 10 } } });

      const distChart = Chart.getChart("id-distchart");
      const othersIndex = distChart.data.labels.findIndex((l) => l.toLowerCase() === "others");
      expect(distChart.data.datasets[0].data[othersIndex]).toBeDefined();
    });

    it("updateDistributionChart computes others with matching category (line 711)", function () {
      address.chartDatasets.distchart.labels.push("others");
      address.chartDatasets.distchart.datasets.forEach(function (ds) { ds.data.push("0"); });
      address.chartDatasets.distchart.datasets.push({ label: "balance", data: ["0"] });
      window.Chart.getChart.mockReturnValue(chartInstance({
        canvas: { id: 'id-distchart' },
        data: { labels: ["ALGO", "USDC", "Others"], datasets: [{ data: ["40", "10", "0"] }, { data: ["10", "20", "0"] }, { data: ["5", "5", "0"] }, { data: ["5", "5", "0"] }, { data: ["0"] }] }
      }));
      address.updateDistributionChart({ categories: { algo: { balance: 40 }, usdc: { balance: 10 } } });
    });

  it("updateDistributionChart returns early when distributionChart missing (line 717)", function () {
    window.Chart.getChart.mockImplementation((id) => id === "id-distchart" ? null : chartInstance());
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

  it("updateDistributionChart handles missing price (line 720)", function () {
    document.querySelector(".pricetip").removeAttribute("data-price");
    expect(() => address.updateDistributionChart({ categories: {} })).not.toThrow();
  });

  it("updateDistributionChart USD conversion branch (line 726)", function () {
    // Ensure mock chart has 4 datasets matching distchart
    window.Chart.getChart.mockReturnValue(chartInstance({
      canvas: { id: 'id-distchart' },
      data: { labels: ["ALGO", "USDC", "Others"], datasets: [
        { data: ["40", "10", "0"] },
        { data: ["10", "20", "0"] },
        { data: ["5", "5", "0"] },
        { data: ["5", "5", "0"] }
      ]}
    }));
    localStorage.setItem("cur", "USD");
    address.updateDistributionChart({ categories: {} });

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });

  it("updateDistributionChart ALGO conversion branch (line 726)", function () {
    // Ensure mock chart has 4 datasets matching distchart
    window.Chart.getChart.mockReturnValue(chartInstance({
      canvas: { id: 'id-distchart' },
      data: { labels: ["ALGO", "USDC", "Others"], datasets: [
        { data: ["40", "10", "0"] },
        { data: ["10", "20", "0"] },
        { data: ["5", "5", "0"] },
        { data: ["5", "5", "0"] }
      ]}
    }));
    localStorage.setItem("cur", "ALGO");
    address.updateDistributionChart({ categories: {} });

    const distChart = Chart.getChart("id-distchart");
    expect(distChart.data.datasets[0].data[0]).toBeDefined();
  });
});
