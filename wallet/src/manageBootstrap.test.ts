/**
 * @jest-environment jsdom
 */

import { initManageAddresses } from "./manageBootstrap";

function jsonResponse(payload: unknown): Response {
  return { json: async () => payload } as Response;
}

describe("initManageAddresses", () => {
  it("no-ops when the container is absent", async () => {
    document.body.innerHTML = "";
    const result = await initManageAddresses();
    expect(result).toBeNull();
  });

  it("mounts and loads when the container is present", async () => {
    document.body.innerHTML = `
      <div id="connected-addresses" data-api-base="/api/v2/wallet">
        <div id="connected-addresses-list"></div>
      </div>`;
    const fetchFn = jest.fn(async () => jsonResponse({ addresses: [] }));
    const component = await initManageAddresses(
      { stepUpSign: jest.fn(), addAddress: jest.fn(), fetchFn },
      document
    );
    expect(component).not.toBeNull();
    expect(fetchFn).toHaveBeenCalledWith(
      "/api/v2/wallet/manage/addresses/",
      expect.anything()
    );
  });

  it("falls back to the default api base when unset", async () => {
    document.body.innerHTML = `
      <div id="connected-addresses">
        <div id="connected-addresses-list"></div>
      </div>`;
    const fetchFn = jest.fn(async () => jsonResponse({ addresses: [] }));
    await initManageAddresses(
      { stepUpSign: jest.fn(), addAddress: jest.fn(), fetchFn },
      document
    );
    expect(fetchFn).toHaveBeenCalledWith(
      "/api/v2/wallet/manage/addresses/",
      expect.anything()
    );
  });
});
