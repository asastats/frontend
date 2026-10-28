import { Capacitor } from "@capacitor/core";

import { AppLock, installAppLock } from "./appLock";

jest.mock("@capacitor/core", () => ({
  Capacitor: { isPluginAvailable: jest.fn() },
  registerPlugin: jest.fn(() => ({ openSettings: jest.fn().mockResolvedValue(undefined) })),
}));

const available = Capacitor.isPluginAvailable as jest.Mock;

describe("installAppLock", () => {
  beforeEach(() => {
    document.body.innerHTML =
      '<li data-app-lock-settings hidden><button type="button" id="lock">App lock</button></li>';
    available.mockReset();
    (AppLock.openSettings as jest.Mock).mockClear();
  });

  it("shows the entry and opens the native settings on a tap", () => {
    available.mockReturnValue(true);

    expect(installAppLock()).toBe(true);
    const entry = document.querySelector<HTMLElement>("[data-app-lock-settings]")!;
    expect(entry.hidden).toBe(false);
    document.getElementById("lock")!.click();
    expect(AppLock.openSettings).toHaveBeenCalledTimes(1);
  });

  it("keeps the entry hidden in a shell without the plugin", () => {
    available.mockReturnValue(false);

    expect(installAppLock()).toBe(false);
    expect(document.querySelector<HTMLElement>("[data-app-lock-settings]")!.hidden).toBe(true);
    expect(AppLock.openSettings).not.toHaveBeenCalled();
  });

  it("does nothing on a page without the entry", () => {
    available.mockReturnValue(true);
    document.body.innerHTML = "";

    expect(installAppLock()).toBe(false);
  });
});
