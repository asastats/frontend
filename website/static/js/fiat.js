/**
 * @file The reader's fiat, read from the first `[data-fiat]` element.
 * `data-fiat` is the code and `data-fiat-rate` the fiat per USD; without
 * both (or with a bad rate) every answer is USD. See docs/logbook.md.
 */
(function (root) {
  "use strict";

  var SYMBOLS = { USD: "$", EUR: "€" };

  /** @returns {Element|null} the element carrying the reader's fiat. */
  function source() {
    return typeof document === "undefined" ? null : document.querySelector("[data-fiat]");
  }

  /** @returns {number} the published rate, or NaN when unusable. */
  function publishedRate(element) {
    var value = element ? parseFloat(element.getAttribute("data-fiat-rate")) : NaN;
    return isFinite(value) && value > 0 ? value : NaN;
  }

  /** @returns {string} the fiat code shown, "USD" unless another is usable. */
  function code() {
    var element = source();
    var chosen = element && element.getAttribute("data-fiat");
    if (!chosen || chosen === "USD" || isNaN(publishedRate(element))) return "USD";
    return chosen;
  }

  /** @returns {number} fiat per USD, 1 for USD. */
  function rate() {
    return code() === "USD" ? 1 : publishedRate(source());
  }

  /**
   * @param {number} usd - an amount in USD
   * @returns {number} the amount in the reader's fiat
   */
  function fromUsd(usd) {
    return usd * rate();
  }

  /** @returns {string} the fiat's symbol, or "" when it has none. */
  function symbol() {
    return SYMBOLS[code()] || "";
  }

  /**
   * The `cur` key holds "ALGO" or a fiat code; any fiat means the fiat side.
   * @param {string|null} stored - the stored choice
   * @returns {boolean}
   */
  function isFiatSide(stored) {
    return !!stored && stored !== "ALGO";
  }

  var api = {
    code: code,
    rate: rate,
    fromUsd: fromUsd,
    symbol: symbol,
    isFiatSide: isFiatSide,
  };
  root.Fiat = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : this);
