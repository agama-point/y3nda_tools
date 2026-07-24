# Agama Point simple ciphers library
# 2017-26

import base64

from cryptography.fernet import Fernet

__version__ = "0.3.0"



class Agama_fernet:
   """Text-oriented wrapper around :class:`cryptography.fernet.Fernet`.

   Fernet keys are URL-safe base64-encoded 32-byte values. With ``nostr=True``,
   :meth:`set_key` accepts a hexadecimal 32-byte key.
   """

   def __init__(self, debug=True):
      self.debug = debug
      self.key = None
      self.cipher_suite = None

   def new_key_generate(self, print_out=True):
      """Generate, configure, and return a Fernet key."""
      key = Fernet.generate_key()
      self.set_key(key)
      if print_out:
         print("[New key generate]")
         print("key_hex:", key.hex())
      return key

   def set_key(self, key, nostr=False):
      """Configure and return a base64 Fernet key.

      The former helper accepted ``nostr=True`` for raw hexadecimal secret
      bytes; retain that API while validating the final key immediately.
      """
      if nostr:
         if isinstance(key, bytes):
            key = key.decode("ascii")
         key_bytes = bytes.fromhex(key)
         # A raw 32-byte Nostr key needs Fernet's base64 representation.
         # Also accept the hexadecimal representation of an existing Fernet
         # key, which was supported by the original helper's callers.
         if len(key_bytes) == 44:
            key = key_bytes
         else:
            key = base64.urlsafe_b64encode(key_bytes)
      elif isinstance(key, str):
         key = key.encode("ascii")

      self.cipher_suite = Fernet(key)
      self.key = key
      return key

   def _get_cipher_suite(self):
      if self.cipher_suite is None:
         raise ValueError("Set or generate a Fernet key before encrypting or decrypting.")
      return self.cipher_suite

   def encrypt(self, plaintext):
      """Encrypt ``plaintext`` and return a URL-safe token as ``str``."""
      if not isinstance(plaintext, str):
         raise TypeError("plaintext must be a str")
      return self._get_cipher_suite().encrypt(plaintext.encode("utf-8")).decode("ascii")

   def decrypt(self, ciphertext):
      """Decrypt a ``str`` or ``bytes`` token and return UTF-8 text."""
      if isinstance(ciphertext, str):
         ciphertext = ciphertext.encode("ascii")
      return self._get_cipher_suite().decrypt(ciphertext).decode("utf-8")


# A conventional spelling for new callers; the original public name remains.
AgamaFernet = Agama_fernet
