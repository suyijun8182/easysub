import hashlib
import secrets
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.migrate import run_migrations
from app.models import ApiToken, User
from app.routers import auth, users
from app.security import create_access_token, hash_password


class ApiTokenSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password('test-password')

    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add(User(id=1, username='alice', email='alice@example.com', password_hash=self.password_hash))
            db.commit()
        app = FastAPI()
        app.include_router(auth.router)
        app.include_router(users.router)
        def local_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = local_db
        self.client = TestClient(app)
        self.headers = {'Authorization': 'Bearer ' + create_access_token(1)}

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def test_new_token_is_hashed_authenticates_and_is_shown_only_once(self):
        response = self.client.post('/api/me/tokens', headers=self.headers, json={'name': 'automation'})
        self.assertEqual(response.status_code, 200, response.text)
        created = response.json()
        plaintext = created['token']
        digest = hashlib.sha256(plaintext.encode()).hexdigest()
        with Session(self.engine) as db:
            stored = db.get(ApiToken, created['id']).token
        self.assertNotEqual(stored, plaintext)
        self.assertEqual(stored, digest)
        self.assertEqual(self.client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + plaintext}).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + digest}).status_code, 401)
        listing = self.client.get('/api/me/tokens', headers=self.headers)
        self.assertEqual(listing.status_code, 200)
        self.assertNotIn(plaintext, listing.text)
        self.assertNotIn(digest, listing.text)
        self.assertEqual(set(listing.json()[0]), {'id', 'name', 'created_at', 'last_used_at'})
        self.assertIsNotNone(listing.json()[0]['last_used_at'])
        self.assertEqual(self.client.delete('/api/me/tokens/' + str(created['id']), headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + plaintext}).status_code, 401)

    def test_legacy_urlsafe_tokens_migrate_once_and_still_authenticate(self):
        legacy = secrets.token_urlsafe(32)
        self.assertEqual(len(legacy), 43)
        with Session(self.engine) as db:
            db.add(ApiToken(user_id=1, name='legacy', token=legacy))
            db.commit()
        run_migrations(self.engine)
        run_migrations(self.engine)
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(ApiToken.token)), hashlib.sha256(legacy.encode()).hexdigest())
        self.assertEqual(self.client.get('/api/auth/me', headers={'Authorization': 'Bearer ' + legacy}).status_code, 200)

    def test_migration_hashes_non_hex_values_and_preserves_hashes(self):
        with Session(self.engine) as db:
            db.add_all([ApiToken(user_id=1, name='non-hex', token='Z' * 64),
                        ApiToken(user_id=1, name='hashed', token=hashlib.sha256(b'existing').hexdigest())])
            db.commit()
        run_migrations(self.engine)
        run_migrations(self.engine)
        with Session(self.engine) as db:
            values = {row.name: row.token for row in db.scalars(select(ApiToken))}
        self.assertEqual(values['non-hex'], hashlib.sha256(('Z' * 64).encode()).hexdigest())
        self.assertEqual(values['hashed'], hashlib.sha256(b'existing').hexdigest())
