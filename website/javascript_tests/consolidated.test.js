const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.collapsible = jest.fn();
$.prototype.animate = jest.fn(function () { return this; });

global.cur = (value) => "C" + value;
global.dec6 = (value) => "D" + value;

let lastConfig;

function chartInstance(overrides) {
  return Object.assign({
    canvas: { id: 'id-asachart' },
    data: { datasets: [{ data: ['10', '20'] }], labels: ['a', 'b'] },
    config: { type: 'pie' },
    legend: { legendItems: [{ hidden: false }, { hidden: false }] },
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

const consolidated = require('../static/js/consolidated.js');

function fixture() {
  return (
    '<script type="application/json" id="consolidated">' +
    '["10","20","5"]</script>' +
    '<script type="application/json" id="distchart">' +
    '{"datasets":[{"data":["10","20"],"label":"Lbl"}],"labels":["a","b"]}' +
    '</script>' +
    '<script type="application/json" id="ratiochart">' +
    '{"datasets":[{"data":["30","70"]}],"labels":["x","y"]}</script>' +
    '<script type="application/json" id="asachart">' +
    '{"datasets":[{"data":["30","70"]}],"labels":["x","y"]}</script>' +
    '<script type="application/json" id="nftchart">' +
    '{"datasets":[{"data":["30","70"]}],"labels":["x","y"]}</script>' +
    '<span class="pricetip" data-price="2" data-total="100" data-totalnft="10"' +
    ' data-totalnftfloor="5" data-totalwnft="200" data-pricealgo="0.5"></span>' +
    '<canvas id="id-distchart"></canvas><div id="id-legend-distchart"></div>' +
    '<canvas id="id-ratiochart"></canvas><div id="id-legend-ratiochart"></div>' +
    '<canvas id="id-asachart"></canvas><div id="id-legend-asachart"></div>' +
    '<canvas id="id-nftchart"></canvas><div id="id-legend-nftchart"></div>' +
    '<ul class="collapsible" id="id-cons"><li><div id="id-cons-body"></div>' +
    '</li></ul>' +
    '<div class="totalnonft"><input type="checkbox"></div>' +
    '<div class="header"><div><div class="unit">a</div></div></div>'
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
});

afterEach(() => {
  jest.useRealTimers();
  jest.resetModules();
});


describe("parseJsonScript", function () {
  it('parses and clones a JSON script element', function () {
    var data = consolidated.parseJsonScript("distchart");
    expect(data.labels).toEqual(["a", "b"]);
    expect(data.datasets[0].data).toEqual(["10", "20"]);
  });
});


describe("getOrCreateLegendList", function () {
  it('creates a ul when none exists', function () {
    var ul = consolidated.getOrCreateLegendList("id-legend-distchart");
    expect(ul.tagName).toBe("UL");
    expect($("#id-legend-distchart ul").length).toBe(1);
  });
  it('reuses an existing ul', function () {
    $("#id-legend-distchart").append("<ul id='existing'></ul>");
    var ul = consolidated.getOrCreateLegendList("id-legend-distchart");
    expect(ul.id).toBe("existing");
  });
});


describe("toggleLegendVisibility", function () {
  it('toggles single item visibility for pie charts', function () {
    var chart = chartInstance();
    consolidated.toggleLegendVisibility(chart, { index: 2 }, "pie");
    expect(chart.toggleDataVisibility).toHaveBeenCalledWith(2);
    expect(chart.update).toHaveBeenCalled();
  });
  it('toggles dataset visibility for non-pie charts', function () {
    var chart = chartInstance({ isDatasetVisible: () => false });
    consolidated.toggleLegendVisibility(chart, { datasetIndex: 1 }, "bar");
    expect(chart.setDatasetVisibility).toHaveBeenCalledWith(1, true);
    expect(chart.update).toHaveBeenCalled();
  });
});


describe("legendClickHandler", function () {
  it('updates chart data for pie charts', function () {
    consolidated.parseJsonScript("asachart");
    var chart = chartInstance({
      canvas: { id: 'id-asachart' },
      config: { type: 'pie' },
      legend: { legendItems: [{ hidden: false }, { hidden: false }] },
    });
    consolidated.legendClickHandler(chart, { index: 0, datasetIndex: 0 });
    expect(chart.update).toHaveBeenCalled();
  });
  it('only toggles for non-pie charts', function () {
    var chart = chartInstance({ config: { type: 'bar' } });
    consolidated.legendClickHandler(chart, { datasetIndex: 0 });
    expect(chart.setDatasetVisibility).toHaveBeenCalled();
  });
});


describe("totalChart", function () {
  it('sums ratiochart with NFT total', function () {
    expect(consolidated.totalChart("ratiochart")).toBeGreaterThan(0);
  });
  it('sums ratiochartfloor with floor value', function () {
    expect(consolidated.totalChart("ratiochartfloor")).toBeGreaterThan(0);
  });
  it('computes asachart total', function () {
    expect(consolidated.totalChart("asachart")).toBe(100 * 2 - 10);
  });
  it('computes nftchart total', function () {
    expect(Number(consolidated.totalChart("nftchart"))).toBe(10);
  });
  it('computes nftfloorchart total', function () {
    expect(Number(consolidated.totalChart("nftfloorchart"))).toBe(5);
  });
  it('converts to USD when selected', function () {
    localStorage.setItem("hcur", "USD");
    expect(consolidated.totalChart("asachart")).toBe((100 * 2 - 10) / 2);
  });
  it('returns zero for an unknown chart name', function () {
    expect(consolidated.totalChart("unknown")).toBe(0);
  });
});


describe("totalChartFiltered", function () {
  it('sums only the visible legend items', function () {
    consolidated.parseJsonScript("distchart");
    var chart = chartInstance({
      legend: { legendItems: [{ hidden: false }, { hidden: true }] },
    });
    expect(consolidated.totalChartFiltered(chart, "distchart")).toBe(10);
  });
});


describe("formatChartTotal", function () {
  it('formats the filtered total with the currency code', function () {
    consolidated.parseJsonScript("asachart");
    var chart = chartInstance({
      legend: { legendItems: [{ hidden: false }, { hidden: false }] },
    });
    expect(consolidated.formatChartTotal(chart, "asachart")).toContain("ALGO");
  });
});


describe("updateChartData", function () {
  it('rescales the dataset and updates the title', function () {
    consolidated.parseJsonScript("asachart");
    var chart = chartInstance({
      canvas: { id: 'id-asachart' },
      data: { datasets: [{ data: ['0', '0'] }] },
      legend: { legendItems: [{ hidden: false }, { hidden: false }] },
    });
    consolidated.updateChartData(chart);
    expect(chart.titleBlock.options.text).toContain("ALGO");
  });
});


describe("updateDistChart", function () {
  it('rescales distchart values in ALGO', function () {
    consolidated.parseJsonScript("distchart");
    var chart = chartInstance({ data: { datasets: [{ data: ['0', '0'] }] } });
    window.Chart.getChart.mockReturnValue(chart);
    consolidated.updateDistChart();
    expect(chart.update).toHaveBeenCalled();
  });
  it('converts distchart values to USD', function () {
    localStorage.setItem("hcur", "USD");
    consolidated.parseJsonScript("distchart");
    var chart = chartInstance({ data: { datasets: [{ data: ['0', '0'] }] } });
    window.Chart.getChart.mockReturnValue(chart);
    consolidated.updateDistChart();
    expect(chart.update).toHaveBeenCalled();
  });
});


describe("setTotalCharts", function () {
  it('sets titles for the pie charts and refreshes distchart', function () {
    ["ratiochart", "asachart", "nftchart", "distchart"].forEach(function (n) {
      consolidated.parseJsonScript(n);
    });
    var dist = chartInstance({ data: { datasets: [{ data: ['0', '0'] }] } });
    window.Chart.getChart.mockImplementation(function (id) {
      return id === 'id-distchart' ? dist : chartInstance();
    });
    consolidated.setTotalCharts();
    expect(dist.update).toHaveBeenCalled();
  });
});


describe("setTotalNoNft (via mainConsolidated)", function () {
  it('returns early when the pricetip is missing', function () {
    $(".pricetip").remove();
    consolidated.mainConsolidated();
    expect(window.Chart).toHaveBeenCalled();
  });
  it('computes the total without NFTs in USD', function () {
    localStorage.setItem("hcur", "USD");
    localStorage.setItem("htotalnonft", "y");
    consolidated.mainConsolidated();
    expect($(".totalnonft input[type=checkbox]").prop("checked")).toBe(true);
  });
  it('computes the total with NFTs in ALGO', function () {
    consolidated.mainConsolidated();
    expect($(".totalnonft input[type=checkbox]").prop("checked")).toBe(false);
  });
});


describe("distribution context formatters", function () {
  function context(extra) {
    return Object.assign({
      chart: { legend: { legendItems: [{ hidden: false }, { hidden: false }] } },
      dataIndex: 0,
      datasetIndex: 0,
      raw: "5",
    }, extra || {});
  }
  it('percentDistAsset in ALGO', function () {
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistAsset(context())).toContain("%");
  });
  it('percentDistAsset in USD', function () {
    localStorage.setItem("hcur", "USD");
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistAsset(context())).toContain("%");
  });
  it('percentDistAsset skips hidden datasets', function () {
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistAsset(context({
      chart: { legend: { legendItems: [{ hidden: true }, { hidden: true }] } },
    }))).toContain("%");
  });
  it('percentDistSection in ALGO', function () {
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistSection(context())).toContain("%");
  });
  it('percentDistSection in USD', function () {
    localStorage.setItem("hcur", "USD");
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistSection(context())).toContain("%");
  });
  it('percentDistSection skips hidden datasets', function () {
    consolidated.parseJsonScript("distchart");
    expect(consolidated.percentDistSection(context({
      chart: { legend: { legendItems: [{ hidden: true }, { hidden: true }] } },
    }))).toContain("%");
  });
  it('valueDistSection returns formatted value', function () {
    expect(consolidated.valueDistSection({ raw: "7" })).toBe("C7 ALGO");
  });
  it('valueSection returns formatted value', function () {
    consolidated.parseJsonScript("asachart");
    expect(consolidated.valueSection("asachart", 0)).toContain("ALGO");
  });
});


describe("populateDistChart", function () {
  it('returns false when the canvas is missing', function () {
    $("#id-distchart").remove();
    expect(consolidated.populateDistChart()).toBe(false);
  });
  it('builds the chart and wires callbacks', function () {
    jest.useFakeTimers();
    consolidated.populateDistChart();
    expect(window.Chart).toHaveBeenCalled();
    var ctx = {
      raw: "5", dataIndex: 0, datasetIndex: 0,
      dataset: { label: "Lbl" },
      chart: { legend: { legendItems: [{ hidden: false }, { hidden: false }] } },
    };
    var cb = lastConfig.options.plugins.tooltip.callbacks;
    expect(typeof cb.label(ctx)).toBe("string");
    expect(typeof cb.footer([ctx])).toBe("string");
    lastConfig.options.onHover(
      { native: { target: { style: {} } } }, [{}]
    );
    lastConfig.options.onHover(
      { native: { target: { style: {} } } }, []
    );
    var canvas = document.getElementById('id-distchart');
    canvas.onclick({});
  });
  it('scrolls and toggles the header on click', function () {
    jest.useFakeTimers();
    consolidated.populateDistChart();
    var inst = window.Chart.mock.instances[0];
    inst.data = { labels: ["a"] };
    inst.getElementsAtEventForMode = jest.fn(() => [{ index: 0 }]);
    var canvas = document.getElementById('id-distchart');
    canvas.onclick({});
    jest.runAllTimers();
  });
  it('handles a click with no matching unit element', function () {
    jest.useFakeTimers();
    consolidated.populateDistChart();
    var inst = window.Chart.mock.instances[0];
    inst.data = { labels: ["nomatch"] };
    inst.getElementsAtEventForMode = jest.fn(() => [{ index: 0 }]);
    document.getElementById('id-distchart').onclick({});
    jest.runAllTimers();
  });
  it('scrolls when the unit is outside the viewport', function () {
    jest.useFakeTimers();
    consolidated.populateDistChart();
    var inst = window.Chart.mock.instances[0];
    inst.data = { labels: ["a"] };
    inst.getElementsAtEventForMode = jest.fn(() => [{ index: 0 }]);
    Object.defineProperty($(".unit")[0], "offsetTop", { value: 100000 });
    document.getElementById('id-distchart').onclick({});
    jest.runAllTimers();
  });
  it('does not toggle when the header is already active', function () {
    jest.useFakeTimers();
    $(".header").wrap('<div class="active"></div>');
    consolidated.populateDistChart();
    var inst = window.Chart.mock.instances[0];
    inst.data = { labels: ["a"] };
    inst.getElementsAtEventForMode = jest.fn(() => [{ index: 0 }]);
    document.getElementById('id-distchart').onclick({});
    jest.runAllTimers();
  });
});


describe("populatePieCharts", function () {
  it('skips missing canvases', function () {
    $("#id-ratiochart, #id-asachart, #id-nftchart").remove();
    expect(consolidated.populatePieCharts()).toBeUndefined();
    expect(window.Chart).not.toHaveBeenCalled();
  });
  it('builds the pie charts and wires callbacks', function () {
    jest.useFakeTimers();
    window.Chart.mockImplementation(function (ctx, config) {
      lastConfig = config;
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => [{ index: 0 }]),
      }));
    });
    consolidated.populatePieCharts();
    expect(window.Chart).toHaveBeenCalledTimes(3);

    var ratioConfig = window.Chart.mock.calls[0][1];
    var asaConfig = window.Chart.mock.calls[1][1];
    var nftConfig = window.Chart.mock.calls[2][1];

    expect(typeof nftConfig.options.plugins.tooltip.callbacks.label(
      { formattedValue: "30", dataIndex: 0 })).toBe("string");

    var hover = { native: { target: { style: {} } } };
    ratioConfig.options.onHover(hover, [{}]);
    asaConfig.options.onHover(hover, [{}]);
    asaConfig.options.onHover(hover, []);

    document.getElementById('id-nftchart').onclick({});
    jest.runAllTimers();
  });

  it('ignores a pie click with no points', function () {
    jest.useFakeTimers();
    window.Chart.mockImplementation(function (ctx, config) {
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => []),
      }));
    });
    consolidated.populatePieCharts();
    document.getElementById('id-nftchart').onclick({});
    jest.runAllTimers();
  });

  it('scrolls on a pie click when the unit is off-screen', function () {
    jest.useFakeTimers();
    window.Chart.mockImplementation(function (ctx, config) {
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => [{ index: 0 }]),
      }));
    });
    consolidated.populatePieCharts();
    Object.defineProperty($(".unit")[0], "offsetTop", { value: 100000 });
    document.getElementById('id-nftchart').onclick({});
    jest.runAllTimers();
  });

  it('does not toggle a pie header that is already active', function () {
    jest.useFakeTimers();
    $(".header").wrap('<div class="active"></div>');
    window.Chart.mockImplementation(function (ctx, config) {
      Object.assign(this, chartInstance({
        data: { labels: ["a"] },
        getElementsAtEventForMode: jest.fn(() => [{ index: 0 }]),
      }));
    });
    consolidated.populatePieCharts();
    document.getElementById('id-nftchart').onclick({});
    jest.runAllTimers();
  });
});


describe("htmlLegendPlugin afterUpdate", function () {
  it('renders the legend items and wires their click', function () {
    consolidated.populateDistChart();
    var plugin = lastConfig.plugins[0];
    var items = [
      { fillStyle: "#fff", strokeStyle: "#000", lineWidth: 1,
        hidden: true, text: "Hidden", index: 0, datasetIndex: 0 },
      { fillStyle: "#000", strokeStyle: "#fff", lineWidth: 2,
        hidden: false, text: "Shown", index: 1, datasetIndex: 0 },
    ];
    var chart = chartInstance({
      config: { type: 'bar' },
      options: { plugins: { legend: { labels: { generateLabels: () => items } } } },
    });
    var container = document.getElementById('id-legend-distchart');
    container.appendChild(document.createElement('ul')).appendChild(
      document.createElement('li')
    );
    plugin.afterUpdate(chart, {}, { containerID: 'id-legend-distchart' });
    var li = container.querySelector('li');
    li.onclick();
    expect(chart.update).toHaveBeenCalled();
  });
});


describe("onConsolidatedClick", function () {
  it('stores h when the body is shown', function () {
    document.getElementById('id-cons-body').style.display = "block";
    consolidated.onConsolidatedClick(null);
    expect(localStorage.setItem).toHaveBeenCalledWith('hcons', 'h');
  });
  it('stores empty when the body is hidden', function () {
    document.getElementById('id-cons-body').style.display = "none";
    consolidated.onConsolidatedClick(null);
    expect(localStorage.setItem).toHaveBeenCalledWith('hcons', '');
  });
});


describe("checkConsolidated", function () {
  it('closes the collapsible when the saved status is hidden', function () {
    var close = jest.fn();
    M.Collapsible.getInstance.mockReturnValue({ close: close });
    consolidated.checkConsolidated('h');
    expect(close).toHaveBeenCalledWith(0);
  });
  it('does nothing for other values', function () {
    consolidated.checkConsolidated('');
    expect(M.Collapsible.getInstance).not.toHaveBeenCalled();
  });
});


describe("mainConsolidated", function () {
  it('initializes the page', function () {
    jest.useFakeTimers();
    consolidated.mainConsolidated();
    expect($.prototype.collapsible).toHaveBeenCalled();
    expect(window.Chart).toHaveBeenCalled();
  });
});
