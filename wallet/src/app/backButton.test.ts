import { App } from "@capacitor/app";

import { closeOverlay, handleBack, installBackButton } from "./backButton";

jest.mock("@capacitor/app", () => ({
  App: {
    addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }),
    minimizeApp: jest.fn().mockResolvedValue(undefined),
  },
}));

function openDialog(): HTMLDialogElement {
  const dialog = document.createElement("dialog");
  dialog.setAttribute("open", "");
  // jsdom has no HTMLDialogElement.close.
  dialog.close = jest.fn(() => dialog.removeAttribute("open"));
  document.body.appendChild(dialog);
  return dialog;
}

describe("closeOverlay", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("closes the topmost open dialog first", () => {
    const first = openDialog();
    const second = openDialog();
    expect(closeOverlay()).toBe(true);
    expect(second.close).toHaveBeenCalled();
    expect(first.close).not.toHaveBeenCalled();
  });

  it("closes an open dropdown menu", () => {
    document.body.innerHTML = '<details class="dropdown" open><summary>Menu</summary></details>';
    expect(closeOverlay(document)).toBe(true);
    expect(document.querySelector("details")!.open).toBe(false);
  });

  it("reports nothing to close", () => {
    document.body.innerHTML = '<details class="dropdown"></details><dialog></dialog>';
    expect(closeOverlay(document)).toBe(false);
  });
});

describe("handleBack", () => {
  const goBack = jest.fn();

  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("closes an overlay instead of going back", () => {
    openDialog();
    handleBack({ canGoBack: true }, document, goBack);
    expect(goBack).not.toHaveBeenCalled();
  });

  it("goes back when there is history", () => {
    handleBack({ canGoBack: true }, document, goBack);
    expect(goBack).toHaveBeenCalled();
  });

  it("minimizes on the first page", () => {
    handleBack({ canGoBack: false }, document, goBack);
    expect(goBack).not.toHaveBeenCalled();
    expect(App.minimizeApp).toHaveBeenCalled();
  });

  it("uses history.back by default", () => {
    const back = jest.spyOn(window.history, "back").mockImplementation(() => undefined);
    handleBack({ canGoBack: true });
    expect(back).toHaveBeenCalled();
    back.mockRestore();
  });
});

describe("installBackButton", () => {
  it("listens for backButton and handles it", () => {
    installBackButton();
    expect(App.addListener).toHaveBeenCalledWith("backButton", expect.any(Function));
    const listener = (App.addListener as jest.Mock).mock.calls[0][1];
    listener({ canGoBack: false });
    expect(App.minimizeApp).toHaveBeenCalled();
  });
});
