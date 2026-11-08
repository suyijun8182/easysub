import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pyotp
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import ApiToken, User
from app.routers import auth, users, admin, backup, notifications
from app.security import create_access_token, create_refresh_token, hash_password


class AccountSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password('test-password')

    def make_engine(self):
        return create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)

    def setUp(self):
        auth._FAILS.clear()
        self.engine = self.make_engine()
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(User(id=1, username='alice', email='alice@example.com', password_hash=self.password_hash, is_admin=True))
            db.add(User(id=2, username='bob', email='bob@example.com', password_hash=self.password_hash))
            db.add(ApiToken(user_id=2, name='script', token='api-test-token'))
            db.commit()
        app = FastAPI()
        for router in (auth.router, users.router, admin.router, backup.router, notifications.router):
            app.include_router(router)
        def local_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = local_db
        self.client = TestClient(app)
        self.headers = {'Authorization': 'Bearer ' + create_access_token(2)}
        self.admin_headers = {'Authorization': 'Bearer ' + create_access_token(1)}

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_enabled_2fa_cannot_be_reset_with_api_token(self):
        secret = pyotp.random_base32()
        with Session(self.engine) as db:
            user = db.get(User, 2)
            user.totp_enabled = True
            user.totp_secret = secret
            db.commit()
        response = self.client.post('/api/me/2fa/setup', headers={'Authorization': 'Bearer api-test-token'})
        self.assertNotEqual(response.status_code, 200)
        with Session(self.engine) as db:
            self.assertTrue(db.get(User, 2).totp_enabled)
            self.assertEqual(db.get(User, 2).totp_secret, secret)

    def test_2fa_rotation_keeps_old_factor_until_confirmed_and_revokes_old_sessions(self):
        secret = pyotp.random_base32()
        with Session(self.engine) as db:
            user = db.get(User, 2); user.totp_enabled = True; user.totp_secret = secret; db.commit()
        setup = self.client.post('/api/me/2fa/setup', headers=self.headers, json={'password': 'test-password', 'code': pyotp.TOTP(secret).now()})
        self.assertEqual(setup.status_code, 200, setup.text)
        with Session(self.engine) as db:
            self.assertTrue(db.get(User, 2).totp_enabled)
            self.assertEqual(db.get(User, 2).totp_secret, secret)
        enabled = self.client.post('/api/me/2fa/enable', headers=self.headers, json={'password': 'test-password', 'code': pyotp.TOTP(setup.json()['secret']).now()})
        self.assertEqual(enabled.status_code, 200, enabled.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).status_code, 401)
        new_headers = {'Authorization': 'Bearer ' + enabled.json()['access_token']}
        self.assertEqual(self.client.get('/api/auth/me', headers=new_headers).status_code, 200)
        self.assertEqual(self.client.post('/api/me/2fa/disable', headers=new_headers, json={'password': 'test-password', 'code': 'invalid'}).status_code, 400)

    def test_password_change_invalidates_access_and_refresh_but_new_login_works(self):
        old_refresh = create_refresh_token(2)
        response = self.client.post('/api/me/password', headers=self.headers, json={'old_password': 'test-password', 'new_password': 'changed-password'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/refresh', json={'refresh_token': old_refresh}).status_code, 401)
        login = self.client.post('/api/auth/login', data={'username': 'bob', 'password': 'changed-password'})
        self.assertEqual(login.status_code, 200, login.text)
        refreshed = self.client.post('/api/auth/refresh', json={'refresh_token': login.json()['refresh_token']})
        self.assertEqual(refreshed.status_code, 200, refreshed.text)

    def test_admin_password_reset_invalidates_old_sessions(self):
        response = self.client.patch('/api/admin/users/2', headers=self.admin_headers, json={'password': 'admin-new-password'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).status_code, 401)

    def test_registration_code_cannot_reset_password(self):
        with Session(self.engine) as db:
            user = db.get(User, 2); user.email_code = '123456'; user.email_code_expires = datetime.now(timezone.utc) + timedelta(minutes=10); db.commit()
        response = self.client.post('/api/auth/reset', json={'email': 'bob@example.com', 'code': '123456', 'new_password': 'attacker-password'})
        self.assertEqual(response.status_code, 400)

    def test_reset_challenge_is_limited_and_password_reset_revokes_sessions(self):
        with patch.object(auth.email_svc, 'smtp_configured', return_value=True), patch.object(auth.email_svc, 'send_reset') as send:
            self.assertEqual(self.client.post('/api/auth/forgot', json={'email': 'bob@example.com'}).status_code, 200)
            code = send.call_args.args[1]
            self.client.post('/api/auth/forgot', json={'email': 'bob@example.com'})
            self.assertEqual(send.call_count, 1)
        for _ in range(5):
            self.client.post('/api/auth/reset', json={'email': 'bob@example.com', 'code': 'bad', 'new_password': 'changed-password'})
        self.assertEqual(self.client.post('/api/auth/reset', json={'email': 'bob@example.com', 'code': code, 'new_password': 'changed-password'}).status_code, 429)
        with Session(self.engine) as db:
            db.get(User, 2).reset_code_attempts = 0; db.commit()
        auth._FAILS.clear()
        response = self.client.post('/api/auth/reset', json={'email': 'bob@example.com', 'code': code, 'new_password': 'changed-password'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/refresh', json={'refresh_token': create_refresh_token(2)}).status_code, 401)

    def test_private_webhook_is_rejected_before_network_request(self):
        with patch('httpx.Client') as client:
            response = self.client.post('/api/notifications/test', headers=self.headers, json={'channel': 'webhook', 'config': {'urls': ['http://127.0.0.1:8000/internal']}})
            self.assertEqual(response.status_code, 502, response.text)
            client.return_value.__enter__.return_value.post.assert_not_called()

    def test_recovery_attempts_for_unknown_email_do_not_lock_another_account(self):
        for _ in range(10):
            self.client.post('/api/auth/reset', json={'email': 'missing@example.com', 'code': 'bad', 'new_password': 'new-password'})
        response = self.client.post('/api/auth/reset', json={'email': 'bob@example.com', 'code': 'bad', 'new_password': 'new-password'})
        self.assertEqual(response.status_code, 400)

    def test_exhausted_email_verification_can_recover_via_throttled_resend(self):
        with Session(self.engine) as db:
            user = db.get(User, 2); user.email_verified = False; user.email_code = '123456'
            user.email_code_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
            user.email_code_attempts = 5; db.commit()
        login = self.client.post('/api/auth/login', data={'username': 'bob', 'password': 'test-password'})
        self.assertEqual(login.json()['detail']['code'], 'EMAIL_VERIFICATION_REQUIRED')
        self.assertEqual(login.json()['detail']['email'], 'bob@example.com')
        with patch.object(auth.email_svc, 'smtp_configured', return_value=True), patch.object(auth.email_svc, 'send_code') as send:
            self.assertEqual(self.client.post('/api/auth/resend-verification', json={'email': 'bob@example.com', 'code': ''}).status_code, 200)
            code = send.call_args.args[1]
            self.client.post('/api/auth/resend-verification', json={'email': 'bob@example.com', 'code': ''})
            self.assertEqual(send.call_count, 1)
        response = self.client.post('/api/auth/verify-email', json={'email': 'bob@example.com', 'code': code})
        self.assertEqual(response.status_code, 200, response.text)

    def test_notification_failure_does_not_expose_secret_urls(self):
        import httpx
        from app.services import notify
        request = httpx.Request('POST', 'https://provider.example/FAKE_SECRET')
        error = httpx.HTTPStatusError('FAKE_SECRET', request=request, response=httpx.Response(400, request=request))
        with patch.object(notify, 'send_one', side_effect=error), patch('app.activity.log') as logged:
            response = self.client.post('/api/notifications/test', headers=self.headers, json={'channel': 'telegram'})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('FAKE_SECRET', response.text)
        logged.assert_called_once()
        self.assertNotIn('FAKE_SECRET', logged.call_args.args[1])


class DisasterRecoveryTests(unittest.TestCase):
    make_engine = AccountSafetyTests.make_engine
    setUpClass = classmethod(AccountSafetyTests.setUpClass.__func__)
    setUp = AccountSafetyTests.setUp
    tearDown = AccountSafetyTests.tearDown

    def test_full_backup_is_password_encrypted_and_restores_2fa_without_old_sessions(self):
        secret = pyotp.random_base32()
        with Session(self.engine) as db:
            user = db.get(User, 2); user.totp_secret = secret; user.totp_enabled = True; db.commit()
        self.assertNotEqual(self.client.get('/api/backup/export-all', headers=self.admin_headers).status_code, 200)
        response = self.client.post('/api/backup/export-all', headers=self.admin_headers, json={'password': 'backup-password-123'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn(secret, response.text)
        self.assertNotIn(self.password_hash, response.text)
        envelope = response.json()
        before = self.client.get('/api/auth/me', headers=self.headers).json()
        wrong = self.client.post('/api/backup/import-all', headers=self.admin_headers, json={'data': envelope, 'password': 'wrong-password', 'replace': True})
        self.assertEqual(wrong.status_code, 400, wrong.text)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).json(), before)
        with Session(self.engine) as db:
            db.get(User, 2).totp_secret = None; db.get(User, 2).totp_enabled = False; db.commit()
        restored = self.client.post('/api/backup/import-all', headers=self.admin_headers, json={'data': envelope, 'password': 'backup-password-123', 'replace': True})
        self.assertEqual(restored.status_code, 200, restored.text)
        with Session(self.engine) as db:
            self.assertTrue(db.get(User, 2).totp_enabled)
            self.assertEqual(db.get(User, 2).totp_secret, secret)
        self.assertEqual(self.client.get('/api/auth/me', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/refresh', json={'refresh_token': create_refresh_token(2)}).status_code, 401)

    def test_old_backup_does_not_disable_existing_2fa(self):
        secret = pyotp.random_base32()
        with Session(self.engine) as db:
            user = db.get(User, 2); user.totp_secret = secret; user.totp_enabled = True; db.commit()
        data = {'users': [{'user': {'username': 'bob'}, 'subscriptions': []}]}
        restored = self.client.post('/api/backup/import-all', headers=self.admin_headers, json={'data': data})
        self.assertEqual(restored.status_code, 200, restored.text)
        with Session(self.engine) as db:
            self.assertTrue(db.get(User, 2).totp_enabled)
            self.assertEqual(db.get(User, 2).totp_secret, secret)

    def test_auto_backup_never_falls_back_to_plaintext(self):
        from app.services import autobackup
        with patch.object(autobackup.settings, 'backup_password', ''), patch.object(autobackup.database, 'SessionLocal') as sessions:
            self.assertIn('skipped', autobackup.run_auto_backup())
            sessions.assert_not_called()
