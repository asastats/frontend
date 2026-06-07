/**
 * @file www.asastats.com browser side logic for consolidated view
 * @author Ivica Paleka
 */

/*
* * * * * * * * * * * * * * * * * * * * * * * * * * *
* SECTION: Initialization
* * * * * * * * * * * * * * * * * * * * * * * * * * *
*/

var chartDatasets = {};


// /**
//  * Call main function upon finished document loading
//  *
//  */
// $(mainConsolidated);


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */


/**
 * Main function
 * @function mainConsolidated
 *
 */
function mainConsolidated() {
  $('.collapsible').collapsible();
  $(".collapsible-header.consolidated").on("click", onConsolidatedClick);
  populateDistChart();
  populatePieCharts();
  setTotalNoNft(localStorage.getItem('htotalnonft') || '');
  checkConsolidated(localStorage.getItem('hcons') || '');
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */


/**
 * Parse JSON script with provided name.
 * @function parseJsonScript
 *
 * @param {String} script Name of JSON script to parse from DOM
 *
 * @returns {Object}
 */
function parseJsonScript(script) {
  chartDatasets[script] = JSON.parse(document.getElementById(script).textContent);
  return JSON.parse(JSON.stringify(chartDatasets[script]));
}


/**
 * Return legend list container element
 * @function getOrCreateLegendList
 *
 * @param {String} id
 *
 * @returns {Object}
 */
function getOrCreateLegendList(id) {
  var legendContainer = document.getElementById(id);
  var listContainer = legendContainer.querySelector('ul');
  if (!listContainer) {
    listContainer = document.createElement('ul');
    listContainer.style.display = 'flex';
    listContainer.style.flexDirection = 'column';
    listContainer.style.margin = 0;
    listContainer.style.padding = 0;
    legendContainer.appendChild(listContainer);
  }
  return listContainer;
};


var htmlLegendPlugin = {
  id: 'htmlLegend',
  afterUpdate: function afterUpdate(chart, args, options) {
    var ul = getOrCreateLegendList(options.containerID);

    // Remove old legend items
    while (ul.firstChild) {
      ul.firstChild.remove();
    }

    // Reuse the built-in legendItems generator
    var items = chart.options.plugins.legend.labels.generateLabels(chart);
    items.forEach(function (item) {
      var li = document.createElement('li');
      li.style.alignItems = 'center';
      li.style.cursor = 'pointer';
      li.style.display = 'flex';
      li.style.flexDirection = 'row';
      li.style.marginLeft = 0;

      li.onclick = function () { legendClickHandler(chart, item) };

      // Color box
      var boxSpan = document.createElement('span');
      boxSpan.style.background = item.fillStyle;
      boxSpan.style.borderColor = item.strokeStyle;
      boxSpan.style.borderWidth = item.lineWidth + 'px';
      boxSpan.style.display = 'inline-block';
      boxSpan.style.flexShrink = 0;
      boxSpan.style.height = '16px';
      boxSpan.style.marginRight = '4px';
      boxSpan.style.width = '16px';

      // Text
      var textContainer = document.createElement('p');
      textContainer.style.color = "#ababab";
      textContainer.style.fontSize = "12px";
      textContainer.style.margin = 0;
      textContainer.style.padding = 0;
      textContainer.style.textDecoration = item.hidden ? 'line-through' : '';
      textContainer.className = "truncate";
      var text = document.createTextNode(item.text);
      textContainer.appendChild(text);
      li.appendChild(boxSpan);
      li.appendChild(textContainer);
      ul.appendChild(li);
    });
  }
};


/**
 * Toggle provided legend item visibility
 * @function toggleLegendVisibility
 *
 * @param {Object} chart
 * @param {Object} item
 * @param {String} type
 *
 */
function toggleLegendVisibility(chart, item, type) {
  if (type === 'pie') {
    // Pie and doughnut charts only have a single dataset and visibility is per item
    chart.toggleDataVisibility(item.index);
  } else {
    chart.setDatasetVisibility(item.datasetIndex, !chart.isDatasetVisible(item.datasetIndex));
  }
  chart.update();
};


/**
 * Update provided chart's dataset
 * @function updateChartData
 *
 * @param {Object} chart
 *
 */
function updateChartData(chart) {
  var name = chart.canvas.id.split("-")[1];
  var totalNew = totalChartFiltered(chart, name);
  for (var i = 0; i < chartDatasets[name].datasets[0].data.length; i++) {
    chart.data.datasets[0].data[i] = (
      100.0 * parseFloat(chartDatasets[name].datasets[0].data[i]) / totalNew
    ).toString();
  }
  chart.titleBlock.options.text = formatChartTotal(chart, name);
};


/**
 * Update distribution chart
 * @function updateDistChart
 *
 */
function updateDistChart() {
  var value = 0;
  var chart = Chart.getChart('id-distchart');
  var code = localStorage.getItem('hcur') || 'ALGO';
  var price = $(".pricetip")[0].dataset.price;
  var datasets = chartDatasets["distchart"].datasets;

  for (var i = 0; i < datasets.length; i++) {
    for (var j = 0; j < datasets[i].data.length; j++) {
      value = parseFloat(chartDatasets["distchart"].datasets[i].data[j]);
      if (code == 'USD') {
        value /= price;
      }
      chart.data.datasets[i].data[j] = value.toString();
    }
  }
  chart.update();
};


/**
 * Handler for legend label click event
 * @function legendClickHandler
 *
 * @param {Object} chart
 * @param {Object} item
 *
 * @returns {Object}
 */
function legendClickHandler(chart, item) {
  var type = chart.config.type;

  toggleLegendVisibility(chart, item, type);

  if (type === 'pie') {
    updateChartData(chart);
    chart.update();
  }
};


/**
 * Calculate and return total for chart defined by provided name
 * @function totalChart
 *
 * @param {String} name
 *
 * @returns {Number}
 */
function totalChart(name) {
  var total = 0;
  var code = localStorage.getItem('hcur') || 'ALGO';
  var price = $(".pricetip")[0].dataset.price;

  if (name == "ratiochart" || name == "ratiochartfloor") {
    var data = JSON.parse(document.getElementById("consolidated").textContent);
    for (var i = 0; i < data.length - 1; i++) {
      total += parseFloat(data[i]);
    }
    if (name == "ratiochartfloor") {
      total += parseFloat(data[data.length - 1]);
    } else {
      total += parseFloat($(".pricetip")[0].dataset.totalnft);
    }
  } else if (name == "asachart" || name == "distchart") {
    total = $(".pricetip")[0].dataset.total * price - $(".pricetip")[0].dataset.totalnft;
  } else if (name == "nftchart") {
    total = $(".pricetip")[0].dataset.totalnft;
  } else if (name == "nftfloorchart") {
    total = $(".pricetip")[0].dataset.totalnftfloor;
  }

  if (code == 'USD') {
    total /= price;
  }

  return total;
};


/**
 * Calculate and return filtered total for chart defined by provided name
 * @function totalChartFiltered
 *
 * @param {Object} chart
 * @param {String} name
 *
 * @returns {Number}
 */
function totalChartFiltered(chart, name) {
  var totalNew = 0;
  var data = chartDatasets[name].datasets[0].data;
  for (var i = 0; i < data.length; i++) {
    if (!chart.legend.legendItems[i].hidden)
      totalNew += parseFloat(data[i]);
  }

  return totalNew;
};


/**
 * Calculate and return formatted chart total value
 * @function formatChartTotal
 *
 * @param {Object} chart
 * @param {String} name
 *
 * @returns {String}
 */
function formatChartTotal(chart, name) {
  var total = totalChart(name);
  var totalNew = totalChartFiltered(chart, name);
  var code = localStorage.getItem('hcur') || 'ALGO';

  return cur(totalNew / 100.0 * total) + " " + code;
};


/**
 * Calculate and set chart total titles
 *
 */
function setTotalCharts() {
  ["ratiochart", "asachart", "nftchart"].forEach(function (name) {
    var chart = Chart.getChart('id-' + name);
    chart.titleBlock.options.text = formatChartTotal(chart, name);
    chart.update();
  });
  updateDistChart();
};


/**
 * Set total value with or without NFTs based on user setting
 *
 * @param {String} value
 *
 */
function setTotalNoNft(value) {
  var elem = $(".pricetip")[0];
  if (typeof elem === "undefined")
    return false;

  var price = elem.dataset.price;
  var pricealgo = elem.dataset.pricealgo;
  var totalwnft = elem.dataset.totalwnft;
  var totalnft = elem.dataset.totalnft;

  var code = localStorage.getItem('hcur') || 'ALGO';
  var total = value === 'y' ? (totalwnft - totalnft) / price : totalwnft / price;

  elem.dataset.total = total;

  if (code == 'USD') {
    $(".pricetip").each(function () {
      this.dataset.tooltip = cur(total * price) + " ALGO (" + dec6(price) + " ALGO/USD)"
      this.innerHTML = cur(total) + " USD";
    });
  } else {
    $(".pricetip").each(function () {
      this.dataset.tooltip = cur(total) + " USD (" + dec6(pricealgo) + " USD/ALGO)";
      this.innerHTML = cur(total * price) + " ALGO";
    });
  }

  $(".totalnonft").find("input[type=checkbox]").prop('checked', value == 'y');

}


/**
 * Calculate and return section's percentage of all assets
 * @function percentDistAsset
 *
 * @param {Object} context
 *
 * @returns {String}
 */
function percentDistAsset(context) {
  var totalNew = 0;
  var code = localStorage.getItem('hcur') || 'ALGO';
  var price = $(".pricetip")[0].dataset.price;
  var datasets = chartDatasets["distchart"].datasets;
  for (var i = 0; i < datasets.length; i++) {
    if (!context.chart.legend.legendItems[i].hidden) {
      totalNew += parseFloat(datasets[i].data[context.dataIndex]);
    }
  }
  if (code == 'USD') {
    totalNew /= price;
  }
  return (100 * parseFloat(context.raw) / totalNew).toFixed(2) + "%";
};


/**
 * Calculate and return section's percentage of current asset
 * @function percentDistSection
 *
 * @param {Object} context
 *
 * @returns {String}
 */
function percentDistSection(context) {
  var totalNew = 0;
  var code = localStorage.getItem('hcur') || 'ALGO';
  var price = $(".pricetip")[0].dataset.price;
  var data = chartDatasets["distchart"].datasets[context.datasetIndex].data;
  for (var i = 0; i < data.length; i++) {
    if (!context.chart.legend.legendItems[context.datasetIndex].hidden) {
      totalNew += parseFloat(data[i]);
    }
  }
  if (code == 'USD') {
    totalNew /= price;
  }
  return (100 * parseFloat(context.raw) / totalNew).toFixed(2) + "%";
};


/**
 * Format and return section's value
 * @function valueDistSection
 *
 * @param {Object} context
 *
 * @returns {String}
 */
function valueDistSection(context) {
  var code = localStorage.getItem('hcur') || 'ALGO';
  return cur(context.raw) + " " + code;
};


/**
 * Calculate and return asset/collection value in ALGO/USD
 * @function valueSection
 *
 * @param {String} name
 * @param {Integer} index
 *
 * @returns {String}
 */
function valueSection(name, index) {
  var total = totalChart(name);
  var code = localStorage.getItem('hcur') || 'ALGO';
  return cur(chartDatasets[name].datasets[0].data[index] * total / 100.0) + " " + code;
};


/**
 * Retrieve distribution chart data and assign them to chart.
 * @function populateDistChart
 *
 */
function populateDistChart() {
  var name = "distchart";
  var canvas = document.getElementById('id-' + name);
  if (canvas === null)
    return false;

  var ctx = canvas.getContext('2d');
  var chart = new Chart(ctx, {
    type: 'bar', data: parseJsonScript(name), options: {
      indexAxis: 'y',
      responsive: true,
      animation: {
        duration: 300
      },
      scales: {
        x: {
          stacked: true,
          position: 'top'
        },
        y: {
          stacked: true,
          ticks: {
            autoSkip: false
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              return " " + percentDistAsset(context) + " | " + valueDistSection(context);
            },
            footer: function (context) {
              return percentDistSection(context[0]) + " of " + context[0].dataset.label;
            }
          }
        },
        title: {
          display: false
        },
        htmlLegend: {
          containerID: 'id-legend-' + name
        },
        legend: {
          display: false,
        }
      },
      onHover: function (evt, elem) {
        evt.native.target.style.cursor = elem[0] ? 'pointer' : 'default';
      },
    },
    plugins: [htmlLegendPlugin]
  });

  canvas.onclick = function (evt) {
    var points = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
    if (points.length) {
      var duration = 250;
      var firstPoint = points[0];
      var label = chart.data.labels[firstPoint.index];
      var unit = $(".unit").filter(function () { return ($(this).text() === label) });
      var unmoved = scrollToView(unit.get(0), duration);
      var header = unit.parent().parent();
      if (!header.parent().hasClass("active"))
        setTimeout(
          function () { header.trigger("click"); },
          unmoved ? 0 : duration
        );
    }
  };
}


/**
 * Retrieve charts data and assign them to charts.
 * @function populatePieCharts
 *
 */
function populatePieCharts() {
  ["ratiochart", "asachart", "nftchart"].forEach(function (name) {
    // ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart"].forEach(function (name) {
    var canvas = document.getElementById('id-' + name);
    if (canvas === null)
      return false;

    var ctx = canvas.getContext('2d');
    var chart = new Chart(ctx, {
      type: 'pie', data: parseJsonScript(name), options: {
        responsive: true,
        animation: {
          duration: 300
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                return " " + context.formattedValue + "% | " + valueSection(name, context.dataIndex);
              }
            }
          },
          title: {
            display: true,
            color: "#ababab",
            position: "bottom",
            align: "center",
            text: ''
          },
          htmlLegend: {
            containerID: 'id-legend-' + name
          },
          legend: {
            display: false,
          }
        },
        onHover: function (evt, elem) {
          if (name.indexOf("ratiochart") === -1)
            evt.native.target.style.cursor = elem[0] ? 'pointer' : 'default';
        }
      },
      plugins: [htmlLegendPlugin]
    });

    canvas.onclick = function (evt) {
      var points = chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
      if (points.length) {
        var duration = 250;
        var firstPoint = points[0];
        var label = chart.data.labels[firstPoint.index];
        var unit = $(".unit").filter(function () { return ($(this).text() === label) });
        var unmoved = scrollToView(unit.get(0), duration);
        var header = unit.parent().parent();
        if (!header.parent().hasClass("active"))
          setTimeout(
            function () { header.trigger("click"); },
            unmoved ? 0 : duration
          );
      }
    };
  });
}


/**
 * Save charts visibility status
 *
 */
function onConsolidatedClick(e) {
  var body = document.getElementById('id-cons-body');
  var value = body.style.display == "block" ? 'h' : '';
  localStorage.setItem('hcons', value);
}


/**
 * Hide charts if last status was hidden
 *
 */
function checkConsolidated(value) {
  if (value === 'h') {
    var elem = document.getElementById('id-cons');
    var instance = M.Collapsible.getInstance(elem);
    instance.close(0);
  }
}


/**
 * Return true if provided element in inside visible area
 *
 * @param {jQuery} element
 */
function isNotVisible(element) {
  if (typeof element === "undefined")
    return false;

  // element's distance form the top of the window
  var offset = element.offsetTop;
  // current vertical position of the scroll bar as starting position
  var visible_area_start = $(window).scrollTop();
  // set ending position
  var visible_area_end = visible_area_start + window.innerHeight;
  // check if offset is not inside calculated boundary
  if (offset < visible_area_start || offset > visible_area_end)
    return true;
  return false;
}


/**
 * Scrolls browser so provided element could be seen
 *
 * @param {jQuery} element
 * @param {Number} duration
 *
 */
function scrollToView(element, duration) {
  if (isNotVisible(element)) {
    // animate scrolling for a period of duration ms until element
    // has been placed in the first third of the screen
    $('html,body').animate({
      scrollTop: element.offsetTop - 2 * window.innerHeight / 3
    }, duration);
    return false; // scroll is triggered
  }
  return true; // scroll is not triggered
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    // * SECTION: Initialization    
    mainConsolidated,
    // * SECTION: Helper functions    
    parseJsonScript,
    getOrCreateLegendList,
    toggleLegendVisibility,
    updateChartData,
    updateDistChart,
    legendClickHandler,
    totalChart,
    totalChartFiltered,
    formatChartTotal,
    setTotalCharts,
    percentDistAsset,
    percentDistSection,
    valueDistSection,
    valueSection,
    populateDistChart,
    populatePieCharts,
    onConsolidatedClick,
    checkConsolidated,
  };
}
