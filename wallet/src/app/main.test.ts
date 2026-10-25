import { Capacitor } from "@capacitor/core";

import { installBackButton } from "./backButton";
import { installDeepLinks } from "./deepLinks";
import { download, installDownloads } from "./downloads";
import { installHaptics } from "./haptics";
import { installLinks } from "./links";
import { install, start } from "./main";
import { checkPush, disablePush, enablePush, installPush } from "./push";
import { installSplash } from "./splash";
import { installStatusBar } from "./statusBar";

jest.mock("@capacitor/core", () => ({
  Capacitor: { isNativePlatform: jest.fn().mockReturnValue(false) },
}));
jest.mock("./backButton", () => ({ installBackButton: jest.fn() }));
jest.mock("./deepLinks", () => ({ installDeepLinks: jest.fn() }));
jest.mock("./downloads", () => ({
  download: jest.fn().mockResolvedValue(true),
  installDownloads: jest.fn(),
}));
jest.mock("./haptics", () => ({ installHaptics: jest.fn() }));
jest.mock("./links", () => ({ installLinks: jest.fn() }));
jest.mock("./push", () => ({
  checkPush: jest.fn(),
  disablePush: jest.fn(),
  enablePush: jest.fn(),
  installPush: jest.fn(),
}));
jest.mock("./splash", () => ({ installSplash: jest.fn() }));
jest.mock("./statusBar", () => ({ installStatusBar: jest.fn() }));

const installers = [
  installSplash,
  installLinks,
  installDownloads,
  installBackButton,
  installDeepLinks,
  installStatusBar,
  installHaptics,
  installPush,
];

describe("app main", () => {
  beforeEach(() => {
    delete window.ASAStatsApp;
  });

  it("publishes window.ASAStatsApp with isApp", () => {
    expect(install().isApp).toBe(true);
    expect(window.ASAStatsApp?.isApp).toBe(true);
  });

  it("exposes download", async () => {
    await expect(install().download("/x.csv")).resolves.toBe(true);
    expect(download).toHaveBeenCalledWith("/x.csv");
  });

  it("exposes the push calls alerts.js makes", () => {
    const api = install();
    expect(api.enablePush).toBe(enablePush);
    expect(api.checkPush).toBe(checkPush);
    expect(api.disablePush).toBe(disablePush);
  });

  it("keeps an API that is already there", () => {
    const existing = {
      isApp: true as const,
      download: jest.fn(),
      enablePush: jest.fn(),
      checkPush: jest.fn(),
      disablePush: jest.fn(),
    };
    window.ASAStatsApp = existing;
    expect(install()).toBe(existing);
  });

  it("wires nothing native without the bridge", () => {
    expect(start()).toBe(false);
    expect(window.ASAStatsApp?.isApp).toBe(true);
    installers.forEach((fn) => expect(fn).not.toHaveBeenCalled());
  });

  it("wires every module with the bridge", () => {
    (Capacitor.isNativePlatform as jest.Mock).mockReturnValueOnce(true);
    expect(start()).toBe(true);
    installers.forEach((fn) => expect(fn).toHaveBeenCalledTimes(1));
  });
});
