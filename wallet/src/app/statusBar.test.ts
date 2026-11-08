import { StatusBar, Style } from "@capacitor/status-bar";

import { installStatusBar, isDark, oklchToLinear, syncStatusBar } from "./statusBar";

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
    ["oklch(0.2 0.1 280)", true],
    ["oklch(37% 0.146 265.522)", true],
    ["oklch(94.51% 0.179 104.32)", false],
    ["oklch(1 0 0)", false],
    ["color(srgb 0 0 0)", false],
  ])("%s -> %s", (color, dark) => {
    expect(isDark(color)).toBe(dark);
  });
});

describe("oklchToLinear", () => {
  it("clamps out-of-gamut channels and ignores other colours", () => {
    const [r, g, b] = oklchToLinear("oklch(94.51% 0.179 104.32)") as number[];
    expect(r).toBe(1);
    expect(g).toBeGreaterThan(0.8);
    expect(b).toBeGreaterThanOrEqual(0);
    expect(oklchToLinear("rgb(0, 0, 0)")).toBeNull();
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

  it("syncs when the page is restored from the back-forward cache", () => {
    document.body.style.backgroundColor = "rgb(255, 255, 255)";
    const observer = installStatusBar(document);
    document.body.style.backgroundColor = "rgb(0, 0, 0)";
    window.dispatchEvent(new Event("pageshow"));
    expect(StatusBar.setStyle).toHaveBeenLastCalledWith({ style: Style.Dark });
    observer.disconnect();
  });

  it("syncs when the phone switches between light and dark", () => {
    let onChange: () => void = () => undefined;
    const query = { addEventListener: jest.fn((_type: string, listener: () => void) => { onChange = listener; }) };
    window.matchMedia = jest.fn().mockReturnValue(query);
    try {
      document.body.style.backgroundColor = "rgb(255, 255, 255)";
      const observer = installStatusBar(document);
      expect(window.matchMedia).toHaveBeenCalledWith("(prefers-color-scheme: dark)");
      expect(query.addEventListener).toHaveBeenCalledWith("change", expect.any(Function));
      document.body.style.backgroundColor = "rgb(0, 0, 0)";
      onChange();
      expect(StatusBar.setStyle).toHaveBeenLastCalledWith({ style: Style.Dark });
      observer.disconnect();
    } finally {
      delete (window as { matchMedia?: unknown }).matchMedia;
    }
  });

  it("listens on the global window for a document without a view", () => {
    const detached = document.implementation.createHTMLDocument();
    const observer = installStatusBar(detached);
    document.body.style.backgroundColor = "rgb(0, 0, 0)";
    detached.body.style.backgroundColor = "rgb(255, 255, 255)";
    window.dispatchEvent(new Event("pageshow"));
    expect(StatusBar.setStyle).toHaveBeenCalled();
    observer.disconnect();
  });

  it("defaults to the global document", () => {
    installStatusBar().disconnect();
    expect(StatusBar.setStyle).toHaveBeenCalled();
  });
});
