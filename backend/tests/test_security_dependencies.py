import base64
import hashlib
import hmac
import json
import unittest
from importlib.metadata import version

from app import security


class SecurityDependencyTests(unittest.TestCase):
    def test_runtime_dependencies_include_all_audited_fixes(self):
        for package, minimum in [('starlette', '1.3.1'), ('cryptography', '50.0.0'), ('python-multipart', '0.0.31')]:
            with self.subTest(package=package):
                self.assertGreaterEqual(tuple(map(int, version(package).split('.'))), tuple(map(int, minimum.split('.'))))

    def test_jwt_uses_pyjwt(self):
        self.assertEqual(security.jwt.__name__, 'jwt')

    def test_existing_standard_hs256_tokens_remain_compatible(self):
        def segment(value):
            return base64.urlsafe_b64encode(json.dumps(value, separators=(',', ':')).encode()).rstrip(b'=')
        body = segment({'alg': 'HS256', 'typ': 'JWT'}) + b'.' + segment({'sub': '42', 'type': 'access', 'av': 3})
        signature = hmac.new(security.settings.jwt_secret.encode(), body, hashlib.sha256).digest()
        token = (body + b'.' + base64.urlsafe_b64encode(signature).rstrip(b'=')).decode()
        self.assertEqual(security.decode_token(token), 42)
        self.assertEqual(security.token_version(token), 3)
        self.assertIsNone(security.decode_token(token, 'refresh'))

    def test_invalid_expired_and_wrong_algorithm_tokens_are_rejected(self):
        self.assertIsNone(security.decode_token('not-a-jwt'))
        for payload in ({'sub': '1', 'type': 'access', 'exp': 1}, {'sub': 'not-an-id', 'type': 'access'}):
            token = security.jwt.encode(payload, security.settings.jwt_secret, algorithm='HS256')
            self.assertIsNone(security.decode_token(token))
        token = security.jwt.encode({'sub': '1', 'type': 'access'}, security.settings.jwt_secret, algorithm='HS384')
        self.assertIsNone(security.decode_token(token))
