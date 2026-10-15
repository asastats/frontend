/**
 * @jest-environment jsdom
 */

"use strict";

const Fiat = require("../static/js/fiat.js");

/** Put the reader's fiat on the page the way the server does. */
function page(code, rate) {
  const attrs = [];
  if (code !== undefined) attrs.push('data-fiat="' + code + '"');
  if (rate !== undefined) attrs.push('data-fiat-rate="' + rate + '"');
  document.body.innerHTML = "<div " + attrs.join(" ") + "></div>";
}

describe("fiat.js", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  test("is exposed on window", () => {
    expect(window.Fiat).toBe(Fiat);
  });

  test("reads EUR and its rate", () => {
    page("EUR", "0.8938");
    expect(Fiat.code()).toBe("EUR");
    expect(Fiat.rate()).toBeCloseTo(0.8938);
    expect(Fiat.fromUsd(100)).toBeCloseTo(89.38);
    expect(Fiat.symbol()).toBe("€");
  });

  test("is USD without the attributes", () => {
    expect(Fiat.code()).toBe("USD");
    expect(Fiat.rate()).toBe(1);
    expect(Fiat.fromUsd(100)).toBe(100);
    expect(Fiat.symbol()).toBe("$");
  });

  test("is USD when the rate is missing, zero or not a number", () => {
    for (const rate of [undefined, "0", "-1", "abc", ""]) {
      page("EUR", rate);
      expect(Fiat.code()).toBe("USD");
      expect(Fiat.rate()).toBe(1);
    }
  });

  test("is USD for USD whatever the rate says", () => {
    page("USD", "0.5");
    expect(Fiat.rate()).toBe(1);
  });

  test("has no symbol for a code it does not know", () => {
    page("CHF", "0.8");
    expect(Fiat.code()).toBe("CHF");
    expect(Fiat.symbol()).toBe("");
  });

  test("reads any stored fiat as the fiat side", () => {
    expect(Fiat.isFiatSide("USD")).toBe(true);
    expect(Fiat.isFiatSide("EUR")).toBe(true);
    expect(Fiat.isFiatSide("ALGO")).toBe(false);
    expect(Fiat.isFiatSide(null)).toBe(false);
    expect(Fiat.isFiatSide("")).toBe(false);
  });
});
