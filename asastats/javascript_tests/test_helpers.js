/*
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 * Helper functions
 * * * * * * * * * * * * * * * * * * * * * * * * * * *
 */

global.getEvents = (element) => {
  var elemEvents = $._data(element, "events");
  var allDocEvnts = $._data(document, "events");
  for (var evntType in allDocEvnts) {
    if (allDocEvnts.hasOwnProperty(evntType)) {
      var evts = allDocEvnts[evntType];
      for (var i = 0; i < evts.length; i++) {
        if ($(element).is(evts[i].selector)) {
          if (elemEvents == null) {
            elemEvents = {};
          }
          if (!elemEvents.hasOwnProperty(evntType)) {
            elemEvents[evntType] = [];
          }
          elemEvents[evntType].push(evts[i]);
        }
      }
    }
  }
  return elemEvents;
}
