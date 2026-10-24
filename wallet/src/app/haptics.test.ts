import { Haptics, ImpactStyle } from "@capacitor/haptics";

import { installHaptics } from "./haptics";

jest.mock("@capacitor/haptics", () => ({
  Haptics: { impact: jest.fn().mockResolvedValue(undefined) },
  ImpactStyle: { Light: "LIGHT" },
}));

describe("installHaptics", () => {
  beforeAll(() => installHaptics());

  beforeEach(() => {
    document.body.innerHTML =
      '<button data-app-haptic><span id="in">copy</span></button>' +
      '<i class="copy" id="copy"></i><button id="plain">x</button>';
  });

  it("taps lightly on a marked element", () => {
    document.getElementById("in")!.click();
    expect(Haptics.impact).toHaveBeenCalledWith({ style: ImpactStyle.Light });
  });

  it("taps lightly on a site.js copy button", () => {
    document.getElementById("copy")!.click();
    expect(Haptics.impact).toHaveBeenCalledTimes(1);
  });

  it("stays still elsewhere", () => {
    document.getElementById("plain")!.click();
    expect(Haptics.impact).not.toHaveBeenCalled();
  });

  it("ignores events without a target element", () => {
    document.dispatchEvent(new MouseEvent("click"));
    expect(Haptics.impact).not.toHaveBeenCalled();
  });
});
