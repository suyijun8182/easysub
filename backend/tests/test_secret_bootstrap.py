import base64
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, crypto, security
from app.database import Base
from app.models import User, SyncRecord, SyncChange, SyncReceipt


def fernet(secret):
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


class SecretBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.previous_dir = os.getcwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)

    def tearDown(self):
        os.chdir(self.previous_dir)
        self.temp.cleanup()

    def test_insecure_secret_is_generated_and_persisted(self):
        from app.secrets_store import INSECURE_SECRETS, resolve_jwt_secret
        for configured in INSECURE_SECRETS:
            secret = resolve_jwt_secret(configured)
            self.assertNotIn(secret, INSECURE_SECRETS)
            self.assertEqual(len(secret), 64)
            self.assertEqual(Path('data/jwt_secret').read_text().strip(), secret)
            self.assertEqual(resolve_jwt_secret(configured), secret)

    def test_strong_secret_does_not_write_file(self):
        from app.secrets_store import resolve_jwt_secret
        self.assertEqual(resolve_jwt_secret('strong-secret-' * 5), 'strong-secret-' * 5)
        self.assertFalse(Path('data/jwt_secret').exists())

    def test_settings_replace_default_and_reject_forged_token(self):
        original = config.get_settings.__wrapped__
        with patch.dict(os.environ, {'JWT_SECRET': 'change-me'}):
            settings = original()
        self.assertNotEqual(settings.jwt_secret, 'change-me')
        self.assertEqual(settings.legacy_jwt_secret, 'change-me')
        forged = security.jwt.encode({'sub': '1', 'type': 'access', 'av': 0}, 'change-me', algorithm='HS256')
        with patch.object(security, 'settings', settings):
            self.assertIsNone(security.decode_token(forged))

    def test_legacy_ciphertexts_are_readable_and_encrypt_rotates_them(self):
        from app.secrets_store import INSECURE_SECRETS
        with patch.object(crypto.settings, 'jwt_secret', 'new-secret-' * 6):
            for secret in INSECURE_SECRETS | {'easysub'}:
                old = 'enc:' + fernet(secret or 'easysub').encrypt(b'preserved-secret').decode()
                self.assertEqual(crypto.decrypt(old), 'preserved-secret')
                fresh = crypto.encrypt(old)
                self.assertEqual(crypto._fernet().decrypt(fresh[4:].encode()), b'preserved-secret')

    def test_migration_rotates_all_secret_fields_and_is_idempotent(self):
        from app.secrets_store import reencrypt_legacy_secrets
        from app.services.notify import _SECRET_FIELDS
        engine = create_engine('sqlite://', poolclass=StaticPool)
        Base.metadata.create_all(engine)
        old = 'enc:' + fernet('change-me').encrypt(b'preserved-secret').decode()
        unknown = 'enc:cannot-decrypt'
        with Session(engine) as db, patch.object(crypto.settings, 'jwt_secret', 'new-secret-' * 6):
            cfg = {ch: {field: old for field in fields} for ch, fields in _SECRET_FIELDS.items()}
            cfg['bark'] = {'urls': ['https://example.com']}
            db.add(User(id=1, username='alice', email='a@example.com', password_hash='unused', notify_config=cfg))
            db.flush()
            db.add(SyncRecord(id='record', user_id=1, kind='preferences', payload=old))
            db.add(SyncChange(user_id=1, seq=1, record_id='record', kind='preferences', version=1, deleted=False, readonly=False, payload=old))
            db.add(SyncReceipt(user_id=1, device_id='device', operation_id='op', fingerprint='digest', payload=old))
            db.add(SyncRecord(id='unknown', user_id=1, kind='preferences', payload=unknown))
            db.commit()
            reencrypt_legacy_secrets(db)
            db.expire_all()
            saved = db.get(User, 1).notify_config
            for ch, fields in _SECRET_FIELDS.items():
                for field in fields:
                    self.assertEqual(crypto._fernet().decrypt(saved[ch][field][4:].encode()), b'preserved-secret')
            self.assertEqual(saved['bark'], cfg['bark'])
            snapshots = []
            for model in (SyncRecord, SyncChange, SyncReceipt):
                rows = db.scalars(select(model)).all()
                for row in rows:
                    if row.payload != unknown:
                        self.assertEqual(crypto._fernet().decrypt(row.payload[4:].encode()), b'preserved-secret')
                snapshots.extend(row.payload for row in rows)
            self.assertEqual(db.get(SyncRecord, 'unknown').payload, unknown)
            reencrypt_legacy_secrets(db)
            db.expire_all()
            self.assertEqual(db.get(User, 1).notify_config, saved)
            self.assertEqual([row.payload for model in (SyncRecord, SyncChange, SyncReceipt) for row in db.scalars(select(model))], snapshots)
        engine.dispose()
