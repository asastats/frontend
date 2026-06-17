import { runStepUp, type RunStepUpDeps } from "./manageBridge";

function deps(overrides: Partial<RunStepUpDeps> = {}): {
  d: RunStepUpDeps;
  calls: { ajaxUrl?: string; ajaxValues?: Record<string, unknown>; signArgs?: unknown[] };
} {
  const calls: any = {};
  const d: RunStepUpDeps = {
    fetchFn: jest.fn().mockResolvedValue({
      json: async () => ({
        prefix: "asastats-auth:",
        nonce: "N1",
        address: "0xprimary",
        chain: "evm",
      }),
    }) as unknown as typeof fetch,
    csrf: "tok",
    apiBase: "/api/v2/wallet",
    opsUrl: "/account/addresses/action/",
    stepUpSign: jest.fn(async (...args: unknown[]) => {
      calls.signArgs = args;
      return { signature: "0xsig" };
    }),
    ajax: jest.fn(async (url: string, values: Record<string, unknown>) => {
      calls.ajaxUrl = url;
      calls.ajaxValues = values;
    }),
    ...overrides,
  };
  return { d, calls };
}

describe("runStepUp", () => {
  it("signs the operation-bound message and posts the proof", async () => {
    const { d, calls } = deps();
    await runStepUp({ operation: "set_primary", targetId: 5 }, d);

    expect(d.fetchFn).toHaveBeenCalledWith(
      "/api/v2/wallet/manage/nonce/",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-CSRFToken": "tok" }),
      })
    );
    expect(calls.signArgs).toEqual([
      "0xprimary",
      "evm",
      "asastats-auth:N1:set_primary:5",
    ]);
    expect(calls.ajaxUrl).toBe("/account/addresses/action/");
    expect(calls.ajaxValues).toEqual({
      operation: "set_primary",
      target_id: 5,
      nonce: "N1",
      chain: "evm",
      signature: "0xsig",
    });
  });

  it("includes the enabled flag for set_login", async () => {
    const { d, calls } = deps();
    await runStepUp({ operation: "set_login", targetId: 7, enabled: true }, d);
    expect(calls.signArgs?.[2]).toBe("asastats-auth:N1:set_login:7");
    expect(calls.ajaxValues).toMatchObject({ operation: "set_login", enabled: true });
  });

  it("coerces a missing enabled to false for set_login", async () => {
    const { d, calls } = deps();
    await runStepUp({ operation: "set_login", targetId: 7 }, d);
    expect(calls.ajaxValues).toMatchObject({ enabled: false });
  });

  it("throws and does not post when the challenge errors", async () => {
    const { d } = deps({
      fetchFn: jest.fn().mockResolvedValue({
        json: async () => ({ error: "No primary address to authorize with" }),
      }) as unknown as typeof fetch,
    });
    await expect(runStepUp({ operation: "set_primary", targetId: 5 }, d)).rejects.toThrow(
      "No primary address to authorize with"
    );
    expect(d.ajax).not.toHaveBeenCalled();
    expect(d.stepUpSign).not.toHaveBeenCalled();
  });

  it("propagates a signer rejection (wrong account)", async () => {
    const { d } = deps({
      stepUpSign: jest.fn().mockRejectedValue(new Error("not your primary")),
    });
    await expect(runStepUp({ operation: "set_primary", targetId: 5 }, d)).rejects.toThrow(
      "not your primary"
    );
    expect(d.ajax).not.toHaveBeenCalled();
  });
});
