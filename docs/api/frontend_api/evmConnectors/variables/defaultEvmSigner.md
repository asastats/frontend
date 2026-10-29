[**wallet-frontend**](../../README.md)

***

[wallet-frontend](../../README.md) / [evmConnectors](../README.md) / defaultEvmSigner

# Variable: defaultEvmSigner

> `const` **defaultEvmSigner**: [`EvmSigner`](../../evmWalletComponent/type-aliases/EvmSigner.md)

Defined in: [evmConnectors.ts:142](https://github.com/asastats/frontend/blob/main/wallet/src/evmConnectors.ts#L142)

Default signer: EIP-191 `personal_sign` of the challenge via viem, imported
lazily so viem only loads when a signature is actually requested.
