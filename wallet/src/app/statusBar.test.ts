import { StatusBar, Style } from "@capacitor/status-bar";

import { installStatusBar, isDark, syncStatusBar } from "./statusBar";

jest.mock("@capacitor/status-bar", () => ({
  StatusBar: { setStyle: jest.fn().mockResolvedValue(undefined) },
  Style: { Dark: "DARK", Light: "LIGHT" },
}));

describe("isDark", () => {
  it.each([
    ["rgb(20, 10, 46)", true],
    ["rgba(0, 0, 0, 1)", true],
    ["rgb(255, 255, 255)", false],
    ["rgb(242 240 250)", false],
    ["oklch(0.2 0.1 280)", false],
  ])("%s -> %s", (color, dark) => {
    expect(isDark(color)).toBe(dark);
  });
});

describe("syncStatusBar", () => {
  it("uses light icons on a dark body", () => {
    document.body.style.backgroundColor = "rgb(20, 10, 46)";
    syncStatusBar(document);
    expect(StatusBar.setStyle).toHaveBeenCalledWith({ style: Style.Dark });
  });

  it("uses dark icons on a light body", () => {
    document.body.style.backgroundColor = "rgb(255, 255, 255)";
    syncStatusBar();
    expect(StatusBar.setStyle).toHaveBeenCalledWith({ style: Style.Light });
  });

  it("falls back to window without a defaultView", () => {
    const doc = document.implementation.createHTMLDocument("x");
    Object.defineProperty(doc, "defaultView", { value: null });
    syncStatusBar(doc);
    expect(StatusBar.setStyle).toHaveBeenCalled();
  });
});

describe("installStatusBar", () => {
  it("syncs now and when the theme changes", async () => {
    document.body.style.backgroundColor = "rgb(255, 255, 255)";
    const observer = installStatusBar(document);
    expect(StatusBar.setStyle).toHaveBeenLastCalledWith({ style: Style.Light });
    document.body.style.backgroundColor = "rgb(0, 0, 0)";
    document.documentElement.setAttribute("data-theme", "dark");
    await Promise.resolve();
    expect(StatusBar.setStyle).toHaveBeenLastCalledWith({ style: Style.Dark });
    observer.disconnect();
  });

  it("defaults to the global document", () => {
    installStatusBar().disconnect();
    expect(StatusBar.setStyle).toHaveBeenCalled();
  });
});
