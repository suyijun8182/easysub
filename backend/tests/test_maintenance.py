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
from app.routers import auth, users, admin
from app.security import create_access_token, create_refresh_token, hash_password


class AccountSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password('test-password')

    def setUp(self):
        auth._FAILS.clear()
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(User(id=1, username='alice', email='alice@example.com', password_hash=self.password_hash, is_admin=True))
            db.add(User(id=2, username='bob', email='bob@example.com', password_hash=self.password_hash))
            db.add(ApiToken(user_id=2, name='script', token='api-test-token'))
            db.commit()
        app = FastAPI()
        for router in (auth.router, users.router, admin.router):
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
