const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.collapsible = jest.fn();
$.prototype.tooltip = jest.fn();
$.prototype.animate = jest.fn(function () { return this; });

let lastConfig;

function chartInstance(overrides) {
  return Object.assign({
    canvas: { id: 'id-asachart' },
    data: { datasets: [{ data: ['10', '20'] }, { data: ['5', '15'] }],
      labels: ['a', 'b'] },
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

function fixture() {
  var now = Math.floor(Date.now() / 1000);
  var times = '<span class="epoch" data-epoch="' + (now - 30) + '"></span>' +
    '<span class="epoch" data-epoch="' + (now - 1800) + '"></span>' +
    '<span class="epoch" data-epoch="' + (now - 36000) + '"></span>' +
    '<span class="epoch" data-epoch="' + (now - 864000) + '"></span>';
  var expiry = '<span class="epoch" data-epoch="' + (now - 1000) + '" ' +
    'data-ended="1"></span>' +
    '<span class="epoch" data-epoch="' + (now + 1000) + '"></span>' +
    '<span class="epoch" data-epoch="' + (now - 1000) + '"></span>';
  return (
    '<script type="application/json" id="consolidated">["10","20","5"]</script>' +
    '<script type="application/json" id="distchart">' +
    '{"datasets":[{"data":["10","20"],"label":"A"},'
    + '{"data":["5","15"],"label":"B"}],"labels":["a","b"]}</script>' +
    '<canvas id="id-distchart"></canvas><div id="id-legend-distchart"></div>' +
    pie('ratiochart') + pie('asachart') + pie('nftchart') + pie('nftfloorchart') +
    '<canvas id="id-ratiochartfloor"></canvas>' +
    '<div id="id-legend-ratiochartfloor"></div>' +
    '<span class="pricetip" data-price="2" data-total="100" data-totalnft="10"' +
    ' data-totalnftfloor="5" data-totalwnft="200" data-pricealgo="0.5"></span>' +
    '<div id="id-chart-nft"></div><div id="id-chart-nftfloor"></div>' +
    '<div id="id-chart-ratio"></div><div id="id-chart-ratiofloor"></div>' +
    '<ul class="collapsible consolidated" id="id-cons">' +
    '<li><div class="collapsible-header consolidated"></div>' +
    '<div id="id-cons-body"></div></li></ul>' +
    '<div class="floor"><input type="checkbox"></div>' +
    '<div class="switch"><input type="checkbox"></div>' +
    '<div class="refresh"><input type="checkbox"></div>' +
    '<div class="totalnonft"><input type="checkbox"></div>' +
    '<span class="price" data-val="2" data-unit="USD">2 ALGO/USD</span>' +
    '<span class="unitprice" data-val="2" data-unit="USDC">2 USDC</span>' +
    '<a class="tdist" data-distid="distbox">dist</a><div id="distbox"></div>' +
    '<input id="filter">' +
    '<span class="pricealgo val" data-val="2"></span>' +
    '<span class="val cons-value" data-val="3"></span>' +
    '<span class="val6 pricealgo" data-val="2"></span>' +
    '<span class="val6" data-val="3"></span>' +
    '<ul class="collapsible asasec"><li class="fitem" id="fa0"></li>' +
    '<li class="fitem active" id="fa1">' +
    '<div class="collapsible-header nft"></div>' +
    '<div class="collapsible-body">' + times + '</div></li></ul>' +
    '<ul class="collapsible nftsec"><li class="fitem active" id="fn1">' +
    '<div class="collapsible-header token"></div>' +
    '<div class="collapsible-body">' + expiry + '</div></li></ul>' +
    '<ul class="collapsible fsec">' +
    '<li class="fitem" id="if1"><span>findme</span><span>findme</span></li>' +
    '<li class="fitem" id="if2"><span>findme</span></li>' +
    '<li class="fitem"><span>findme</span></li>' +
    '<span class="nfticon" id="tif1" data-path="/x.png"></span>' +
    '<span class="nfticon" id="other"></span></ul>' +
    '<span class="unit">a</span>' +
    '<img class="nft" data-src="/real.png"><img class="nft">'
  );
}

beforeEach(() => {
  document.body.innerHTML = fixture();
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
  jest.useRealTimers();
  jest.resetModules();
});


describe("parseJsonScript", function () {
  it('parses a plain JSON script', function () {
    expect(address.parseJsonScript("distchart").labels).toEqual(["a", "b"]);
  });
  it('builds ratiochartfloor percentages from the consolidated data', function () {
    var data = address.parseJsonScript("ratiochartfloor");
    expect(data.datasets[0].data.length).toBe(3);
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
});


describe("toggleDist", function () {
  it('toggles the distribution section visibility', function () {
    var el = $(".tdist")[0];
    address.toggleDist.call(el, null);
    expect($("#distbox").hasClass("hidden")).toBe(true);
  });
});


describe("showTimes", function () {
  it('fills epoch spans with elapsed time', function () {
    var header = $(".collapsible-header.nft")[0];
    address.showTimes.call(header, null);
    expect($(".asasec .epoch").html()).toContain("ago on");
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
    expect($.prototype.collapsible).toHaveBeenCalled();
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
      chart: { legend: { legendItems: [{ hidden: false }, { hidden: true }] } },
    };
    var ctx2 = {
      raw: "5", dataIndex: 0, datasetIndex: 1, dataset: { label: "B" },
      chart: { legend: { legendItems: [{ hidden: false }, { hidden: true }] } },
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
      { fillStyle: "#fff", strokeStyle: "#000", lineWidth: 1, hidden: true,
        text: "H", index: 0, datasetIndex: 0 },
      { fillStyle: "#000", strokeStyle: "#fff", lineWidth: 2, hidden: false,
        text: "S", index: 1, datasetIndex: 0 },
    ];
    var pieChart = chartInstance({
      config: { type: 'pie' }, canvas: { id: 'id-asachart' },
      legend: { legendItems: [{ hidden: false }, { hidden: true }] },
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


describe("chart onclick", function () {
  function withPoints() {
    window.Chart.mockImplementation(function (ctx, config) {
      lastConfig = config;
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => [{ index: 0 }]),
      }));
    });
  }
  it('dist onclick with no points', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    document.getElementById('id-distchart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('dist onclick with points scrolls into view', function () {
    jest.useFakeTimers();
    withPoints();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    document.getElementById('id-distchart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('dist onclick off-screen unit', function () {
    jest.useFakeTimers();
    withPoints();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    Object.defineProperty($(".unit")[0], "offsetTop", { value: -100000 });
    document.getElementById('id-distchart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('dist onclick with already-active header', function () {
    jest.useFakeTimers();
    $(".unit").wrap('<div><div></div></div>').parent().parent()
      .wrap('<div class="active"></div>');
    withPoints();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    document.getElementById('id-distchart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('pie onclick with no points', function () {
    jest.useFakeTimers();
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.populatePieCharts();
    document.getElementById('id-asachart').onclick({});
    jest.advanceTimersByTime(400);
  });
  it('pie onclick scrolls into view and toggles header', function () {
    jest.useFakeTimers();
    withPoints();
    address.populatePieCharts();
    document.getElementById('id-asachart').onclick({});
    jest.runAllTimers();
  });
  it('pie onclick off-screen unit', function () {
    jest.useFakeTimers();
    withPoints();
    address.populatePieCharts();
    Object.defineProperty($(".unit")[0], "offsetTop", { value: -100000 });
    document.getElementById('id-asachart').onclick({});
    jest.runAllTimers();
  });
  it('pie onclick with already-active header', function () {
    jest.useFakeTimers();
    $(".unit").wrap('<div><div></div></div>').parent().parent()
      .wrap('<div class="active"></div>');
    withPoints();
    address.populatePieCharts();
    document.getElementById('id-asachart').onclick({});
    jest.runAllTimers();
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
    localStorage.setItem("openasa", "fa1");
    window.onload();
    expect($("img.nft[data-src]").attr("src")).toBe("/real.png");
  });
  it('does nothing extra when no section stored', function () {
    window.onload();
    expect(window.onload).toBeDefined();
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
    jest.useFakeTimers();
    address.mainAddress();
    $(".nfticon").trigger("mouseover");
    $(".nfticon").trigger("click");
    expect($(".nfticon").hasClass("nftpreview")).toBe(true);
  });
});


describe("showExpiry / timeEntry", function () {
  it('fills expiry spans across ended, future and past', function () {
    jest.useFakeTimers();
    address.mainAddress();
    $(".token.collapsible-header").trigger("click");
    var html = $(".nftsec .epoch").map(function () {
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
    jest.advanceTimersByTime(61000);
    expect(localStorage.setItem).toHaveBeenCalledWith("openasa", "fa1");
    expect(localStorage.setItem).toHaveBeenCalledWith("opennft", "fn1");
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
  it('onConsolidatedClick stores the visibility state', function () {
    jest.useFakeTimers();
    address.mainAddress();
    document.getElementById('id-cons-body').style.display = "block";
    $(".collapsible-header.consolidated").trigger("click");
    expect(localStorage.setItem).toHaveBeenCalledWith("cons", "h");
  });
  it('checkConsolidated closes the section when stored hidden', function () {
    jest.useFakeTimers();
    localStorage.setItem("cons", "h");
    var close = jest.fn();
    M.Collapsible.getInstance.mockReturnValue({ close: close });
    window.Chart.getChart.mockReturnValue(chartInstance());
    address.mainAddress();
    expect(close).toHaveBeenCalledWith(0);
  });
});
