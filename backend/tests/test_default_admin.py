import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import config, security
from app.database import Base, get_db
from app.models import User
from app.routers import auth
from app.seed import seed_all


class DefaultAdminTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weak_hash = security.hash_password('admin123')
        cls.strong_hash = security.hash_password('a-strong-password')

    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        app = FastAPI()
        app.include_router(auth.router)
        def local_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = local_db
        self.client = TestClient(app)
        auth._FAILS.clear()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_default_admin_password_is_empty(self):
        self.assertEqual(config.Settings(_env_file=None).admin_password, '')

    def test_empty_or_example_password_does_not_seed_admin_and_first_registration_is_admin(self):
        for password in ('', 'admin123'):
            with self.subTest(password=password):
                with Session(self.engine) as db, patch.object(config.settings, 'admin_password', password):
                    db.query(User).delete()
                    seed_all(db)
                    self.assertIsNone(db.scalar(select(User)))
                response = self.client.post('/api/auth/register', json={
                    'username': 'first', 'email': 'first@example.com', 'password': 'a-strong-password'})
                self.assertEqual(response.status_code, 200, response.text)
                with Session(self.engine) as db:
                    self.assertTrue(db.scalar(select(User)).is_admin)

    def test_explicit_strong_password_still_seeds_admin(self):
        with Session(self.engine) as db, patch.object(config.settings, 'admin_password', 'a-strong-password'):
            seed_all(db)
            user = db.scalar(select(User))
            self.assertTrue(user.is_admin)
            self.assertTrue(security.verify_password('a-strong-password', user.password_hash))

    def test_me_warns_for_default_password_and_rechecks_changed_hash(self):
        with Session(self.engine) as db:
            db.add(User(id=1, username='legacy', email='legacy@example.com', password_hash=self.weak_hash))
            db.commit()
        headers = {'Authorization': 'Bearer ' + security.create_access_token(1)}
        with patch.object(security, 'verify_password', wraps=security.verify_password) as verify:
            for _ in range(2):
                response = self.client.get('/api/auth/me', headers=headers)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()['insecure_default_password'])
            self.assertEqual(verify.call_count, 1)
            with Session(self.engine) as db:
                db.get(User, 1).password_hash = self.strong_hash
                db.commit()
            response = self.client.get('/api/auth/me', headers=headers)
            self.assertFalse(response.json()['insecure_default_password'])
            self.assertEqual(verify.call_count, 2)
