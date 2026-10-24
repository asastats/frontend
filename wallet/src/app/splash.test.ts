import { SplashScreen } from "@capacitor/splash-screen";

import { installSplash } from "./splash";

jest.mock("@capacitor/splash-screen", () => ({
  SplashScreen: { hide: jest.fn().mockResolvedValue(undefined) },
}));

describe("installSplash", () => {
  it("hides at once when the document is parsed", () => {
    installSplash(document);
    expect(SplashScreen.hide).toHaveBeenCalledTimes(1);
  });

  it("waits for DOMContentLoaded while the document is loading", () => {
    const doc = document.implementation.createHTMLDocument("x");
    Object.defineProperty(doc, "readyState", { value: "loading" });
    installSplash(doc);
    expect(SplashScreen.hide).not.toHaveBeenCalled();
    doc.dispatchEvent(new Event("DOMContentLoaded"));
    doc.dispatchEvent(new Event("DOMContentLoaded"));
    expect(SplashScreen.hide).toHaveBeenCalledTimes(1);
  });

  it("defaults to the global document", () => {
    installSplash();
    expect(SplashScreen.hide).toHaveBeenCalled();
  });
});
