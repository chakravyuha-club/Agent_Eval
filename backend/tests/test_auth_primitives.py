"""Pure-python tests (no FastAPI/DB): password hashing, legacy upgrade, login throttle."""
import hashlib
import os
import unittest

from app.core.passwords import (DUMMY_HASH, hash_password, validate_password_strength, verify_and_check_rehash)
from app.core.ratelimit import LoginThrottle


class Passwords(unittest.TestCase):
    def test_roundtrip_and_wrong(self):
        h = hash_password("Correct-Horse-9")
        self.assertEqual(verify_and_check_rehash("Correct-Horse-9", h), (True, False))
        self.assertEqual(verify_and_check_rehash("nope", h), (False, False))

    def test_unique_salts(self):
        self.assertNotEqual(hash_password("Same-Password-1"), hash_password("Same-Password-1"))

    def test_legacy_hash_from_original_code_verifies_and_flags_rehash(self):
        salt = os.urandom(16).hex()
        legacy = "pbkdf2_sha256$%s$%s" % (salt, hashlib.pbkdf2_hmac("sha256", b"AdminSecret2026!", salt.encode(), 100000).hex())
        self.assertEqual(verify_and_check_rehash("AdminSecret2026!", legacy), (True, True))
        self.assertFalse(verify_and_check_rehash("bad", legacy)[0])

    def test_garbage_never_raises(self):
        for g in ("", "x", "a$b", "pbkdf2_sha256$1$2$3$4", None):
            self.assertEqual(verify_and_check_rehash("p", g), (False, False))

    def test_dummy_hash_is_valid_format(self):
        self.assertEqual(verify_and_check_rehash("anything", DUMMY_HASH)[0], False)

    def test_strength_policy(self):
        for bad in ("short1A", "alllowercase123", "ALLUPPER12345", "NoDigitsHereAtAll"):
            with self.assertRaises(ValueError):
                validate_password_strength(bad)
        validate_password_strength("Team01NewPass2026!")


class Throttle(unittest.TestCase):
    def test_lockout_and_recovery(self):
        t = [0.0]
        th = LoginThrottle(3, 60, 100, clock=lambda: t[0])
        for _ in range(3):
            self.assertTrue(th.check("k")[0]); th.record_failure("k")
        ok, retry = th.check("k")
        self.assertFalse(ok); self.assertGreater(retry, 0)
        t[0] = 101
        self.assertTrue(th.check("k")[0])

    def test_success_resets_and_keys_are_independent(self):
        th = LoginThrottle(2, 60, 100)
        th.record_failure("a"); th.record_success("a"); th.record_failure("a")
        self.assertTrue(th.check("a")[0])
        th.record_failure("b"); th.record_failure("b")
        self.assertFalse(th.check("b")[0]); self.assertTrue(th.check("a")[0])

    def test_old_failures_expire_from_window(self):
        t = [0.0]
        th = LoginThrottle(3, 10, 100, clock=lambda: t[0])
        th.record_failure("k"); th.record_failure("k"); t[0] = 20; th.record_failure("k")
        self.assertTrue(th.check("k")[0])


if __name__ == "__main__":
    unittest.main()
