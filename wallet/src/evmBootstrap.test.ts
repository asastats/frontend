/**
 * @jest-environment jsdom
 */

import { initEvm } from "./evmBootstrap";
import type { EvmConnector } from "./evmWalletComponent";
import { EVM_RESUME_KEY, type RestoredProvider } from "./walletResumeEvm";

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
      document.querySelectorAll("#evm-wallet-list [data-wallet-connect]")
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

  describe("after a restart in the app", () => {
    const ADDRESS = "0xf74bbabffd0e455934b2b450ea391d59410cf361";

    function page(projectId = "pid-123") {
      document.body.innerHTML = `
        <div id="evm-wallet-connect" data-wc-project-id="${projectId}">
          <div id="evm-wallet-list"></div>
        </div>`;
    }

    function restored(): RestoredProvider {
      return {
        request: jest.fn(),
        disconnect: jest.fn(),
        session: { topic: "t", namespaces: { eip155: { accounts: [`eip155:1:${ADDRESS}`] } } },
        signer: { client: { core: { history: { values: [], delete: jest.fn() } } } },
      };
    }

    beforeEach(() => {
      localStorage.clear();
      document.documentElement.classList.add("in-app");
    });

    afterEach(() => {
      document.documentElement.classList.remove("in-app");
    });

    it("finishes this page's WalletConnect step", async () => {
      page();
      localStorage.setItem(EVM_RESUME_KEY, JSON.stringify({ kind: "connect", url: window.location.href, at: Date.now() }));
      const restore = jest.fn(async () => restored());
      await initEvm({ connectorFactory: async () => [], signer: jest.fn(), restore });
      expect(restore).toHaveBeenCalledWith("pid-123");
      expect(localStorage.getItem(EVM_RESUME_KEY)).toBeNull();
      expect(document.querySelector("[data-notice]")!.textContent).toContain("connected before your phone closed");
    });

    it("loads no WalletConnect without a step", async () => {
      page();
      const restore = jest.fn();
      await initEvm({ connectorFactory: async () => [], signer: jest.fn(), restore });
      expect(restore).not.toHaveBeenCalled();
    });

    it("does nothing without a project id", async () => {
      page("");
      localStorage.setItem(EVM_RESUME_KEY, JSON.stringify({ kind: "connect", url: window.location.href, at: Date.now() }));
      const restore = jest.fn();
      await initEvm({ connectorFactory: async () => [], signer: jest.fn(), restore });
      expect(restore).not.toHaveBeenCalled();
    });

    it("does nothing on the website", async () => {
      document.documentElement.classList.remove("in-app");
      page();
      localStorage.setItem(EVM_RESUME_KEY, JSON.stringify({ kind: "connect", url: window.location.href, at: Date.now() }));
      const restore = jest.fn();
      await initEvm({ connectorFactory: async () => [], signer: jest.fn(), restore });
      expect(restore).not.toHaveBeenCalled();
    });

    it("does nothing for a document without a window", async () => {
      const doc = document.implementation.createHTMLDocument("");
      doc.body.innerHTML = '<div id="evm-wallet-connect" data-wc-project-id="pid"></div>';
      doc.documentElement.classList.add("in-app");
      const restore = jest.fn();
      await initEvm({ connectorFactory: async () => [], signer: jest.fn(), restore }, doc);
      expect(restore).not.toHaveBeenCalled();
    });
  });
});
