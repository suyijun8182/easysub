import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import User
from app.routers import auth
from app.security import hash_password


class LoginThrottleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password('correct-password')

    def setUp(self):
        auth._FAILS.clear()
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(User(username='alice', email='alice@example.com', password_hash=self.password_hash))
            db.commit()
        app = FastAPI()
        app.include_router(auth.router)
        def local_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = local_db
        self.client_a = TestClient(app, client=('192.0.2.1', 1000))
        self.client_b = TestClient(app, client=('192.0.2.2', 1000))

    def tearDown(self):
        self.client_a.close()
        self.client_b.close()
        self.engine.dispose()
        auth._FAILS.clear()

    def login(self, client, password, username='alice'):
        return client.post('/api/auth/login', data={'username': username, 'password': password})

    def test_attacker_cannot_lock_out_another_ip(self):
        for _ in range(8):
            self.assertEqual(self.login(self.client_a, 'wrong').status_code, 401)
        self.assertEqual(self.login(self.client_b, 'correct-password').status_code, 200)
        self.assertEqual(self.login(self.client_a, 'correct-password').status_code, 429)
        self.assertEqual(self.login(self.client_a, 'wrong', 'ALICE').status_code, 429)

    def test_ip_limit_prevents_username_spraying(self):
        for i in range(30):
            self.assertEqual(self.login(self.client_a, 'wrong', f'unknown-{i}').status_code, 401)
        self.assertEqual(self.login(self.client_a, 'correct-password').status_code, 429)
        self.assertEqual(self.login(self.client_b, 'correct-password').status_code, 200)

    def test_success_clears_only_ip_username_failures(self):
        for _ in range(7):
            self.login(self.client_a, 'wrong')
        self.assertEqual(self.login(self.client_a, 'correct-password').status_code, 200)
        for _ in range(7):
            self.assertEqual(self.login(self.client_a, 'wrong').status_code, 401)
        self.assertEqual(self.login(self.client_a, 'correct-password').status_code, 200)
        for i in range(16):
            self.assertEqual(self.login(self.client_a, 'wrong', f'unknown-{i}').status_code, 401)
        self.assertEqual(self.login(self.client_a, 'correct-password').status_code, 429)
