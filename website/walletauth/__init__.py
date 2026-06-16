"""Wallet-connect address authorization app.

Proves control of an Algorand address by verifying an off-chain signed
0-ALGO self-payment that carries a server-issued nonce, then authorizes the
proven address onto ``request.user.profile``. The signed transaction is never
submitted to the network.
"""
