/**
 * @file www.asastats.com browser side logic address page functions
 * @author Ivica Paleka
 */

/*
* * * * * * * * * * * * * * * * * * * * * * * * * * *
* SECTION: Initialization
* * * * * * * * * * * * * * * * * * * * * * * * * * *
*/

var refreshInterval = 0;
var chartDatasets = {};


/**
 * Call main function upon finished document loading
 *
 */
$(mainAddress);


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Initialization
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Select all NFT images elements and call defer function on them.
 * @function initAddress
 *
 */
function initAddress() {
  deferImages(document.getElementsByClassName('nft'));
  refreshInterval = 0;
  checkOpened("asa");
  checkOpened("nft");
}


/**
 * Assign window onload method to initIndex function.
 * That function will be triggered after all the page content has been already loaded.
 *
 */
window.onload = initAddress;


/**
 * Main function
 * @function mainAddress
 *
 */
function mainAddress() {
  $('.collapsible').collapsible();
  $('.pricetip').tooltip();
  $('.val').tooltip({ "enterDelay": 800 });
  $(".collapsible-header.consolidated").on("click", onConsolidatedClick);
  $(".floor").find("input[type=checkbox]").on("change", toggleNftFloor);
  $(".switch").find("input[type=checkbox]").on("change", toggleCurrency);
  $(".refresh").find("input[type=checkbox]").on("change", toggleRefresh);
  $(".totalnonft").find("input[type=checkbox]").on("change", toggleTotalNoNft);
  $(".price").on("click", togglePrice);
  $(".unitprice").on("click", toggleUnitPrice);
  $(".tdist").on("click", toggleDist);
  populateDistChart();
  populatePieCharts();
  setCurrency(localStorage.getItem('cur') || 'ALGO');
  setRefresh(localStorage.getItem('refresh') || '');
  setTotalNoNft(localStorage.getItem('totalnonft') || '');
  setNftFloor(localStorage.getItem('nftfloor') || '');
  checkConsolidated(localStorage.getItem('cons') || '');
  $("#filter").on("keypress", filterChange);
  $(".nft.collapsible-header").on("click", showTimes);
  $(".token.collapsible-header").on("click", showExpiry);
  $(".nfticon").on("mouseover", nftShowTooltip);
  $(".nfticon").on("click", nftHideTooltip);
  setInterval(timerIncrement, 1000);
  $(this).mousemove(resetTimer);
  $(this).keypress(resetTimer);

}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Assign src attribute from element's dataset src attribute.
 * This is done after all the page content has been already loaded.
 * @function deferImages
 *
 * @param {Array.<object>} images Array of image elements
 *
 */
function deferImages(images) {
  for (var i = 0; i < images.length; i++) {
    if (images[i].getAttribute('data-src')) {
      images[i].setAttribute('src', images[i].getAttribute('data-src'));
    }
  }
}


/**
 * Return true if provided element in inside visible area
 *
 * @param {jQuery} element
 */
function isNotVisible(element) {
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
 * Return true if provided item is inside output array
 *
 * @param {Number} item
 * @param {Array.Number} array
 */
function isItemInArray(item, array) {
  if (typeof item === "undefined")
    return true;

  for (var i = 0; i < array.length; i++) {
    if (array[i] === item) {
      return true;
    }
  }
  return false;
}


/**
 * Return array of list items that contain provided text
 *
 * @param {String} text
 */
function getNodesThatContain(text) {
  var ids = [];
  // var items = [];
  var textNodes = $(".fitem").find(":not(iframe, script, style)")
    .contents().filter(
      function () {
        return this.nodeType == 3
          && this.textContent.toLowerCase().indexOf(text.toLowerCase()) > -1;
      });

  textNodes.parent().each(function (index) {
    var item = $(this).parents('.fitem');
    if (!(isItemInArray(item.attr("id"), ids))) {
      ids.push(item.attr("id"));
      // items.push(item);
    }
  });
  // return items;
  return ids;
}


/**
 * Show items found in all provided arrays
 *
 * @param {Array.Number} matches
 */
function showMatchedNodes(matches) {
  $(".collapsible").not(".consolidated").hide();
  $(".fitem").hide();
  $(".nfticon").hide();
  if (matches.length === 0)
    return false;

  var common = matches.shift().filter(function (v) {
    return matches.every(function (a) {
      return a.indexOf(v) !== -1;
    });
  });

  common.forEach(function (id, index) {
    $("#" + id).show();
    $("#" + id).parents(".fitem").show();
    $("#" + id).parents(".collapsible").show();
    $("#" + id).parents(".collapsible").find(".nfticon").each(function (idx) {
      if ($(this).attr("id") === "t" + id)
        $(this).show();
    });
  });
}


/**
 * Change visibility of all accordions based on text entered
 *
 * @param {jQuery} evt
 */
function filterChange(evt) {
  var keys = [13, 32, 44, 108, 188];
  if (keys.indexOf(evt.keyCode) > -1) {
    var filter = $("#filter").val();
    if (filter == "") {
      $(".fitem").show();
      $(".collapsible").not(".consolidated").show();
      $(".nfticon").show();
    } else {
      var matches = [];
      var array = filter.split(" ");
      if (filter.split(",").length > array.length)
        array = filter.split(",");
      for (var i = 0; i < array.length; i++) {
        matches[i] = getNodesThatContain(array[i]);
      }
      showMatchedNodes(matches);
    }
  }
}


/**
 * Parse JSON script with provided name.
 * @function parseJsonScript
 *
 * @param {String} script Name of JSON script to parse from DOM
 *
 * @returns {Object}
 */
function parseJsonScript(script) {
  if (script == "ratiochartfloor") {
    var data = JSON.parse(document.getElementById("consolidated").textContent);
    var total = 0;
    var percentages = [];
    for (var i = 0; i < data.length; i++) {
      total += parseFloat(data[i]);
    }
    for (var i = 0; i < data.length; i++) {
      percentages.push((100 * parseFloat(data[i]) / total).toString());
    }
    chartDatasets[script] = JSON.parse(document.getElementById("ratiochart").textContent);
    chartDatasets[script].datasets[0].data = percentages;
  } else {
    chartDatasets[script] = JSON.parse(document.getElementById(script).textContent);
  }
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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  var code = localStorage.getItem('cur') || 'ALGO';

  return cur(totalNew / 100.0 * total) + " " + code;
};


/**
 * Calculate and set chart total titles
 *
 */
function setTotalCharts() {
  ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart"].forEach(function (name) {
    var chart = Chart.getChart('id-' + name);
    chart.titleBlock.options.text = formatChartTotal(chart, name);
    chart.update();
  });
  updateDistChart();
};


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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  var code = localStorage.getItem('cur') || 'ALGO';
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
  ["ratiochart", "ratiochartfloor", "asachart", "nftchart", "nftfloorchart"].forEach(function (name) {
    var canvas = document.getElementById('id-' + name);
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
  localStorage.setItem('cons', value);
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
 * Set visibility of NFT and NFT floor charts based on provided value
 *
 * @param {String} value
 *
 */
function setNftFloor(value) {
  var nftdiv = document.getElementById('id-chart-nft');
  var nftfloordiv = document.getElementById('id-chart-nftfloor');
  var ratiodiv = document.getElementById('id-chart-ratio');
  var ratiofloordiv = document.getElementById('id-chart-ratiofloor');

  if (value === 'y') {
    nftdiv.classList.remove('scale-in');
    nftdiv.classList.add('scale-out');
    ratiodiv.classList.remove('scale-in');
    ratiodiv.classList.add('scale-out');

    setTimeout(() => {
      nftdiv.style.display = 'none';
      ratiodiv.style.display = 'none';

      nftfloordiv.classList.remove('scale-out');
      nftfloordiv.classList.add('scale-in');
      ratiofloordiv.classList.remove('scale-out');
      ratiofloordiv.classList.add('scale-in');

      nftfloordiv.style.display = 'block';
      nftfloordiv.classList.add('valign-wrapper');
      nftfloordiv.style.display = 'flex';
      ratiofloordiv.style.display = 'block';
      ratiofloordiv.classList.add('valign-wrapper');
      ratiofloordiv.style.display = 'flex';
    }, 300);

  } else {
    nftfloordiv.classList.remove('scale-in');
    nftfloordiv.classList.add('scale-out');
    ratiofloordiv.classList.remove('scale-in');
    ratiofloordiv.classList.add('scale-out');

    setTimeout(() => {
      nftfloordiv.style.display = 'none';
      ratiofloordiv.style.display = 'none';

      nftdiv.classList.remove('scale-out');
      nftdiv.classList.add('scale-in');
      ratiodiv.classList.remove('scale-out');
      ratiodiv.classList.add('scale-in');

      nftdiv.style.display = 'block';
      nftdiv.classList.add('valign-wrapper');
      nftdiv.style.display = 'flex';
      ratiodiv.style.display = 'block';
      ratiodiv.classList.add('valign-wrapper');
      ratiodiv.style.display = 'flex';
    }, 300);

  }

  $(".floor").find("input[type=checkbox]").prop('checked', value == 'y');
}


/**
 * Switch visibility of NFT and NFT floor charts
 *
 */
function toggleNftFloor(e) {
  var value = $(this).prop('checked') ? 'y' : '';
  localStorage.setItem('nftfloor', value);
  setNftFloor(value);
}


/**
 * Hide NFT preview upon clicking on its thumbnail
 *
 * @param {jQuery} elem
 *
 */
function nftHideTooltip(elem) {
  $(".nftpreview").tooltip('close');
}


/**
 * Show NFT preview upon hovering on its thumbnail
 *
 * @param {jQuery} elem
 *
 */
function nftShowTooltip(elem) {
  $(this).addClass("tooltiped nftpreview");
  $(".nftpreview").tooltip({
    exitDelay: 0,
    unsafeHTML: "<img src='" + this.dataset.path + "' >"
  });
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


/**
 * Represent provided interval base on its size
 *
 * @param {Number} interval
 *
 */
function timeEntry(interval) {
  var prefix;
  if (interval < 91) {
    prefix = Math.round(interval) + " seconds";
  } else if (interval < 5460) {
    prefix = Math.round(interval / 60) + " minutes";
  } else if (interval < 133200) {
    prefix = Math.round(interval / 3600) + " hours";
  } else {
    prefix = Math.round(interval / 86400) + " days";
  }
  return prefix;
}


/**
 * Show how much time passed for children NFT purchases
 *
 * @param {jQuery} evt Triggered click event
 *
 */
function showExpiry(elem) {
  var interval;
  var now = Date.now();
  $(this).siblings(".collapsible-body").find("span.epoch").each(function () {
    interval = parseInt(this.dataset.epoch) - now / 1000;
    isEnded = parseInt(this.dataset.epoch) - now / 1000;
    if (this.dataset.ended) {
      this.innerHTML = "Ended " + timeEntry(Math.abs(interval)) + " ago on ";
    } else {
      if (interval > 0)
        this.innerHTML = timeEntry(interval) + " to expire on ";
      else
        this.innerHTML = "Expired " + timeEntry(Math.abs(interval)) + " ago on ";
    }
  });
}


/**
 * Show how much time passed for children NFT purchases
 *
 * @param {jQuery} evt Triggered click event
 *
 */
function showTimes(elem) {
  var interval;
  var now = Date.now();
  $(this).siblings(".collapsible-body").find("span.epoch").each(function () {
    interval = now / 1000 - parseInt(this.dataset.epoch);
    this.innerHTML = timeEntry(interval) + " ago on ";
  });
}


/**
 * Switch price to the reciprocal one
 * @function togglePrice
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function togglePrice(event) {
  var reciprocal = event.target.innerHTML.indexOf("ALGO/") !== -1 ? false : true;
  if (reciprocal) {
    this.innerHTML = parseFloat(this.dataset.val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 8 }) + " ALGO/" + this.dataset.unit;
  } else {
    this.innerHTML = parseFloat(1.0 / this.dataset.val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 8 }) + " " + this.dataset.unit + "/ALGO";
  }
}


/**
 * Switch unit price to the reciprocal one
 * @function toggleUnitPrice
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function toggleUnitPrice(event) {
  var code = localStorage.getItem('cur') || 'ALGO';
  var price = $(".pricetip")[0].dataset.price;

  var value = this.dataset.val;

  if (code == 'USD') {
    value = value / price;
  }

  var reciprocal = event.target.innerHTML.indexOf(this.dataset.unit) !== -1 ? false : true;
  if (reciprocal) {
    this.innerHTML = parseFloat(1.0 / value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 }) + " " + this.dataset.unit + "/" + code;
  } else {
    this.innerHTML = parseFloat(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 }) + " " + code;
  }
}


/**
 * Shows provided number as currency
 *
 * @param {jQuery} num
 *
 */
function cur(num) {
  return parseFloat(num).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}


/**
 * Shows provided number as 6 digits decimal
 *
 * @param {jQuery} num
 *
 */
function dec6(num) {
  return parseFloat(num).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 6 });
}


/**
 * Calculate and set currency values based on provided currency code
 *
 * @param {String} code
 *
 */
function setCurrency(code) {
  var price = $(".pricetip")[0].dataset.price;
  var pricealgo = $(".pricetip")[0].dataset.pricealgo;
  var total = $(".pricetip")[0].dataset.total;
  if (code == 'USD') {
    $(".pricetip").each(function () {
      this.dataset.tooltip = cur(total * price) + " ALGO (" + dec6(price) + " ALGO/USD)"
      this.innerHTML = cur(total) + " USD";
    });
    $("span.val").each(function () {
      if ($(this).hasClass("pricealgo"))
        this.innerHTML = dec6(price) + " ALGO/USD";
      else
        this.innerHTML = cur(this.dataset.val / price) + " USD";
      this.dataset.tooltip = cur(this.dataset.val) + " ALGO";
      if ($(this).hasClass("cons-value"))
        this.dataset.position = 'bottom';
      else
        this.dataset.position = 'right';
    });
    $("span.val6").each(function () {
      if ($(this).hasClass("pricealgo"))
        this.innerHTML = dec6(price) + " ALGO/USD";
      else
        this.innerHTML = parseFloat(this.dataset.val / price).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 6 }) + " USD";
    });
  } else {
    $(".pricetip").each(function () {
      this.dataset.tooltip = cur(total) + " USD (" + dec6(pricealgo) + " USD/ALGO)";
      this.innerHTML = cur(total * price) + " ALGO";
    });
    $("span.val").each(function () {
      if ($(this).hasClass("pricealgo"))
        this.innerHTML = dec6(pricealgo) + " USD/ALGO";
      else
        this.innerHTML = cur(this.dataset.val) + " ALGO";
      this.dataset.tooltip = cur(this.dataset.val / price) + " USD";
      if ($(this).hasClass("cons-value"))
        this.dataset.position = 'bottom';
      else
        this.dataset.position = 'right';
    });
    $("span.val6").each(function () {
      if ($(this).hasClass("pricealgo"))
        this.innerHTML = dec6(pricealgo) + " USD/ALGO";
      else
        this.innerHTML = parseFloat(this.dataset.val).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 6 }) + " ALGO";
    });
  }
  setTotalCharts();

  $(".switch").find("input[type=checkbox]").prop('checked', code == 'USD');
}


/**
 * Switch amounts from ALGO to USD back and forth
 *
 */
function toggleCurrency() {
  var code = $(this).prop('checked') ? 'USD' : 'ALGO';
  localStorage.setItem('cur', code);
  setCurrency(code);
}


/**
 * Switch visibility of the ASA distribution section
 *
 * @param {jQuery} event Triggered click event object
 *
 */
function toggleDist(event) {
  $("#" + this.dataset.distid).toggleClass("hidden");
  $(this).parent().toggleClass("z-depth-1 asar");
}


/**
 * Switch total without NFTs on and off
 *
 */
function toggleTotalNoNft() {
  var value = $(this).prop('checked') ? 'y' : '';
  localStorage.setItem('totalnonft', value);
  setTotalNoNft(value);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: Auto-refresh
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/**
 * Check if a collapsible section should be opened
 *
 * @param {String} section
 *
 */
function checkOpened(section) {
  var id = localStorage.getItem("open" + section) || ''
  if (id != '') {
    $('.collapsible.' + section + 'sec').children().each(function (index) {
      if ($(this).attr("id") == id) {
        $('.collapsible.' + section + 'sec').collapsible('open', index);
        localStorage.removeItem('open' + section);
        return;
      }
    });
  }
}


/**
 * Reload page and reopen the same accordions
 *
 */
function reloadPage() {
  $('.collapsible.asasec').find('.fitem.active').each(function () {
    localStorage.setItem('openasa', $(this).attr("id"));
  });
  $('.collapsible.nftsec').find('.fitem.active').each(function () {
    localStorage.setItem('opennft', $(this).attr("id"));
  });
  window.location.reload();
}


/**
 * Reset timer used to check for inactivity
 *
 */
function resetTimer() {
  refreshInterval = 0;
}


/**
 * Set refresh value based on provided value
 *
 * @param {String} value
 *
 */
function setRefresh(value) {
  $(".refresh").find("input[type=checkbox]").prop('checked', value == 'y');
}


/**
 * Set total value with or without NFTs based on user setting
 *
 * @param {String} value
 *
 */
function setTotalNoNft(value) {
  var price = $(".pricetip")[0].dataset.price;
  var pricealgo = $(".pricetip")[0].dataset.pricealgo;
  var totalwnft = $(".pricetip")[0].dataset.totalwnft;
  var totalnft = $(".pricetip")[0].dataset.totalnft;

  var code = localStorage.getItem('cur') || 'ALGO';
  var total = value === 'y' ? (totalwnft - totalnft) / price : totalwnft / price;

  $(".pricetip")[0].dataset.total = total;

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
 * Increase timer by one
 *
 */
function timerIncrement() {
  refreshInterval += 1;
  if (refreshInterval > 60 && (localStorage.getItem('refresh') || '') == 'y') {
    refreshInterval = 0;
    reloadPage();
  }
}

/**
 * Switch auto-refresh on and off
 *
 */
function toggleRefresh() {
  var value = $(this).prop('checked') ? 'y' : '';
  localStorage.setItem('refresh', value);
  setRefresh(value);
}


/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * SECTION: exports needed by jest testing framework
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

/* istanbul ignore next */
if (typeof exports !== 'undefined') {
  module.exports = {
    mainAddress,
    isNotVisible,
    parseJsonScript,
    populatePieCharts,
    scrollToView,
    showTimes,
    setCurrency,
    toggleCurrency,
    toggleDist,
    togglePrice,
    toggleUnitPrice,
  };
}
