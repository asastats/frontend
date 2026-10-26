import { App } from "@capacitor/app";

import { installResume } from "./resume";

jest.mock("@capacitor/app", () => ({
  App: { addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }) },
}));

describe("installResume", () => {
  it("fires online on the window when the app resumes", () => {
    const online = jest.fn();
    window.addEventListener("online", online);
    installResume();

    const [event, listener] = (App.addListener as jest.Mock).mock.calls[0];
    expect(event).toBe("resume");
    expect(online).not.toHaveBeenCalled();

    listener();

    expect(online).toHaveBeenCalledTimes(1);
    window.removeEventListener("online", online);
  });
});
