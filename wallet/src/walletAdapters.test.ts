/**
 * @jest-environment jsdom
 */

import {
  ADAPTER_FACTORIES,
  getWalletAdapters,
  createWalletManager,
  uint8ArrayToBase64,
} from "./walletAdapters";
import { WalletManager } from "@txnlab/use-wallet";

describe("walletAdapters", () => {
  describe("uint8ArrayToBase64", () => {
    it("encodes small Uint8Array correctly", () => {
      const bytes = Uint8Array.from([1, 2, 3, 4, 5]);
      expect(uint8ArrayToBase64(bytes)).toBe(btoa(String.fromCharCode(1, 2, 3, 4, 5)));
    });

    it("encodes large Uint8Array without stack overflow", () => {
      const size = 100_000;
      const bytes = new Uint8Array(size);
      for (let i = 0; i < size; i++) {
        bytes[i] = i % 256;
      }
      const b64 = uint8ArrayToBase64(bytes);
      expect(typeof b64).toBe("string");
      expect(b64.length).toBeGreaterThan(0);
      const decoded = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      expect(decoded.length).toBe(size);
      expect(decoded[0]).toBe(0);
      expect(decoded[255]).toBe(255);
    });

    it("encodes empty Uint8Array", () => {
      expect(uint8ArrayToBase64(new Uint8Array(0))).toBe("");
    });
  });

  describe("getWalletAdapters", () => {
    it("returns default adapters when no descriptors provided", () => {
      const adapters = getWalletAdapters();
      expect(adapters.length).toBe(4);
      expect(adapters.map((a) => a.id)).toEqual(["pera", "defly", "lute", "kibisis"]);
    });

    it("returns default adapters when empty list provided", () => {
      const adapters = getWalletAdapters([]);
      expect(adapters.length).toBe(4);
    });

    it("maps string descriptors to matching adapter configs", () => {
      const adapters = getWalletAdapters(["pera", "defly"]);
      expect(adapters.length).toBe(2);
      expect(adapters.map((a) => a.id)).toEqual(["pera", "defly"]);
    });

    it("maps object descriptors to matching adapter configs", () => {
      const adapters = getWalletAdapters([{ id: "pera" }, { id: "lute" }]);
      expect(adapters.length).toBe(2);
      expect(adapters.map((a) => a.id)).toEqual(["pera", "lute"]);
    });

    it("filters out unsupported wallet IDs like exodus", () => {
      const adapters = getWalletAdapters([
        { id: "pera" },
        { id: "exodus" },
        { id: "kibisis" },
      ]);
      expect(adapters.length).toBe(2);
      expect(adapters.map((a) => a.id)).toEqual(["pera", "kibisis"]);
    });

    it("falls back to default adapters if all provided descriptors are unknown", () => {
      const adapters = getWalletAdapters([{ id: "exodus" }, { id: "unknown" }]);
      expect(adapters.length).toBe(4);
      expect(adapters.map((a) => a.id)).toEqual(["pera", "defly", "lute", "kibisis"]);
    });

    it("ignores items with empty or missing id", () => {
      const adapters = getWalletAdapters([{ id: "" }, {} as any, "pera"]);
      expect(adapters.length).toBe(1);
      expect(adapters[0].id).toBe("pera");
    });
  });

  describe("createWalletManager", () => {
    it("instantiates a WalletManager with default network mainnet", () => {
      const manager = createWalletManager([{ id: "pera" }]);
      expect(manager).toBeInstanceOf(WalletManager);
      expect(manager.wallets.length).toBe(1);
      expect(manager.wallets[0].id).toBe("pera");
    });
  });

  describe("ADAPTER_FACTORIES", () => {
    it("has entries for pera, defly, lute, kibisis", () => {
      expect(Object.keys(ADAPTER_FACTORIES).sort()).toEqual(
        ["defly", "kibisis", "lute", "pera"].sort()
      );
    });
  });
});
