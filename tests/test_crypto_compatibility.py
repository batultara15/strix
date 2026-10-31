"""Exercise native crypto bindings used by the packaged CLI, including Intel Mac builds."""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def test_native_crypto_authenticated_roundtrip() -> None:
    # Fixed, synthetic test material only; never use this key/nonce in an application.
    cipher = AESGCM(bytes(32))
    nonce = bytes(12)
    ciphertext = cipher.encrypt(nonce, b"strix-package-smoke", b"package-check")
    assert cipher.decrypt(nonce, ciphertext, b"package-check") == b"strix-package-smoke"


def test_native_crypto_signature_roundtrip() -> None:
    key = Ed25519PrivateKey.generate()
    message = b"strix-package-smoke"
    signature = key.sign(message)
    key.public_key().verify(signature, message)
