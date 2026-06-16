/**
 * @jest-environment jsdom
 */

import { initEvm } from "./evmBootstrap";
import type { EvmConnector } from "./evmWalletComponent";

function connector(): EvmConnector {
  return {
    id: "io.metamask",
    name: "MetaMask",
    connect: jest.fn(async () => ({
      provider: { request: jest.fn() },
      address: "0x52908400098527886E0F7030069857D2E4169EE7",
    })),
  };
}

describe("initEvm", () => {
  it("no-ops and returns null without a container", async () => {
    document.body.innerHTML = `<div></div>`;
    const result = await initEvm({
      connectorFactory: jest.fn(),
      signer: jest.fn(),
    });
    expect(result).toBeNull();
  });

  it("returns null with no arguments when no container is present", async () => {
    document.body.innerHTML = `<div></div>`;
    expect(await initEvm()).toBeNull();
  });

  it("mounts the component and renders connectors with injected deps", async () => {
    document.body.innerHTML = `
      <div id="evm-wallet-connect" data-api-base="/api/v2/wallet/link" data-wc-project-id="pid-123">
        <div id="evm-wallet-list"></div>
      </div>`;
    const connectorFactory = jest.fn(async () => [connector()]);
    const signer = jest.fn(async () => "0xsig");

    const component = await initEvm({ connectorFactory, signer });

    expect(component).not.toBeNull();
    expect(connectorFactory).toHaveBeenCalledWith("pid-123");
    expect(
      document.querySelectorAll("#evm-wallet-list .evm-connect-button")
    ).toHaveLength(1);
  });

  it("passes an empty project id through when the attribute is absent", async () => {
    document.body.innerHTML = `
      <div id="evm-wallet-connect">
        <div id="evm-wallet-list"></div>
      </div>`;
    const connectorFactory = jest.fn(async () => [] as EvmConnector[]);
    await initEvm({ connectorFactory, signer: jest.fn() });
    expect(connectorFactory).toHaveBeenCalledWith("");
  });
});
