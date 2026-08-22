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

let reloadMock;
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
  reloadMock = jest.fn();
  delete window.location;
  window.location = { reload: reloadMock };
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
  it('reloads the page after inactivity when refresh is on', function () {
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
  it('resetTimer is wired to document activity', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress.call(document);
    $(document).trigger("mousemove");
    $(document).trigger("keypress");
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


describe("setCurrency on the money-column designs", function () {
  it('leaves that page alone entirely', function () {
    // Design 1's currency writer writes `innerHTML` -- number *and* unit --
    // into every `span.val`. On the money column each figure pairs with a
    // separate unit element, so it left the asset header reading "253.74 ALGO"
    // beside a sibling still saying "ALGO", and destroyed the nested span in
    // every venue subtotal. It ran on every load, because `mainAddress` calls
    // it unconditionally with the stored currency. `toolbar.js` owns currency
    // there now.
    var page = document.createElement("div");
    page.className = "money-page";
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


describe("setTotalNoNft on the money-column designs", function () {
  it('leaves the headline to the toolbar', function () {
    // It writes `.pricetip` reading design 1's own global `cur` key, so on the
    // money page the total was written by design 1 on load and by nobody
    // afterwards: a reader who had ever chosen USD got a USD headline in a
    // fresh tab, and pressing USD in that page's toolbar changed every figure
    // except the one at the top.
    var page = document.createElement("div");
    page.className = "money-page";
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
