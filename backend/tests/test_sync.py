import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import User, Subscription, Category, SyncRecord, SyncChange, SyncReceipt
from app.routers import auth, subscriptions, sync, backup
from app.security import hash_password, create_access_token
from app.services.sync import capture, lock_account


class SyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("test-password")

    def make_engine(self):
        return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    def setUp(self):
        self.engine = self.make_engine()
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            db.add_all([User(id=1, username="alice", email="alice@example.test", password_hash=self.password_hash), User(id=2, username="bob", email="bob@example.test", password_hash=self.password_hash)])
            db.commit()
        app = FastAPI()
        for router in (auth.router, subscriptions.router, sync.router, backup.router):
            app.include_router(router)
        def local_db():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = local_db
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer " + create_access_token(1)}
        self.other_headers = {"Authorization": "Bearer " + create_access_token(2)}
        self.cap = self.client.get("/api/sync/v1/capabilities", headers=self.headers).json()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def changes(self, cursor=0, limit=200):
        response = self.client.get("/api/sync/v1/changes", params={"cursor": cursor, "limit": limit, "epoch": self.cap["epoch"]}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def push(self, operations):
        return self.client.post("/api/sync/v1/push", json={"epoch": self.cap["epoch"], "device_id": "device-a", "operations": operations}, headers=self.headers)

    def create_web(self, name="Netflix"):
        response = self.client.post("/api/subscriptions", json={"name": name, "amount": 12, "trial_end": "2026-12-01", "card_last4": "1234", "notes": "full note"}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_registration_error_is_distinct_only_for_sync_client(self):
        r = self.client.post("/api/auth/login", data={"username": "missing", "password": "x", "sync_client": "true"})
        self.assertEqual(r.json()["detail"]["code"], "ACCOUNT_NOT_REGISTERED")
        r = self.client.post("/api/auth/login", data={"username": "alice", "password": "wrong", "sync_client": "true"})
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("ACCOUNT_NOT_REGISTERED", r.text)

    def test_web_write_journal_is_complete_and_unchanged_pull_has_no_new_version(self):
        self.create_web()
        first = self.changes()
        sub = next(c for c in first["changes"] if c["kind"] == "subscriptions")
        self.assertEqual(sub["data"]["trial_end"], "2026-12-01")
        self.assertEqual(sub["data"]["card_last4"], "1234")
        self.assertEqual(sub["data"]["notes"], "full note")
        self.assertEqual(self.changes(first["next_cursor"])["changes"], [])

    def test_push_updates_website_and_retries_do_not_apply_twice(self):
        web = self.create_web()
        record = next(c for c in self.changes()["changes"] if c["kind"] == "subscriptions")
        operation = {"op_id": "edit-one", "kind": "subscriptions", "id": record["id"], "base_version": record["version"], "data": {**record["data"], "name": "Updated", "next_renewal_date": "2026-12-12"}}
        first = self.push([operation])
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["results"][0]["status"], "applied")
        self.assertEqual(self.push([operation]).json()["results"], first.json()["results"])
        self.assertEqual(self.client.get(f"/api/subscriptions/{web['id']}", headers=self.headers).json()["name"], "Updated")
        self.assertEqual(self.client.get(f"/api/subscriptions/{web['id']}", headers=self.other_headers).status_code, 404)

    def test_conflict_preserves_server_data_and_delete_is_tombstone(self):
        web = self.create_web()
        old = next(c for c in self.changes()["changes"] if c["kind"] == "subscriptions")
        self.client.put(f"/api/subscriptions/{web['id']}", json={"name": "Web wins only by user choice"}, headers=self.headers)
        result = self.push([{"op_id": "offline-change", "kind": "subscriptions", "id": old["id"], "base_version": old["version"], "data": {**old["data"], "name": "Offline version"}}]).json()["results"][0]
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["server"]["data"]["name"], "Web wins only by user choice")
        response = self.client.request("DELETE", f"/api/subscriptions/{web['id']}", json={"password": "test-password"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.changes()["changes"][-1]["deleted"])

    def test_bulk_sql_is_captured_and_rollback_does_not_publish(self):
        web = self.create_web()
        start = self.changes()["next_cursor"]
        with Session(self.engine) as db:
            lock_account(db, 1)
            db.execute(update(Subscription).where(Subscription.id == web["id"]).values(remark="bulk"))
            db.commit()
        changes = self.changes(start)["changes"]
        self.assertEqual(changes[-1]["data"]["remark"], "bulk")
        start = self.changes()["next_cursor"]
        with Session(self.engine) as db:
            lock_account(db, 1)
            db.get(Subscription, web["id"]).name = "Rolled back"
            capture(db, 1)
            db.rollback()
        self.assertEqual(self.changes(start)["changes"], [])

    def test_foreign_record_and_invalid_relation_are_rejected(self):
        self.create_web()
        record = next(c for c in self.changes()["changes"] if c["kind"] == "subscriptions")
        body = {"epoch": self.client.get("/api/sync/v1/capabilities", headers=self.other_headers).json()["epoch"], "device_id": "other", "operations": [{"op_id": "steal", "kind": "subscriptions", "id": record["id"], "base_version": record["version"], "data": record["data"]}]}
        response = self.client.post("/api/sync/v1/push", json=body, headers=self.other_headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["results"][0]["status"], "applied")
        result = self.push([{"op_id": "bad-relation", "kind": "subscriptions", "id": "11111111-1111-4111-8111-111111111111", "base_version": 0, "data": {"name": "Bad", "category_id": "22222222-2222-4222-8222-222222222222"}}]).json()["results"][0]
        self.assertEqual(result["status"], "rejected")

    def test_journal_payload_and_receipts_do_not_store_plaintext_secrets(self):
        with Session(self.engine) as db:
            lock_account(db, 1)
            user = db.get(User, 1)
            from app.services.notify import apply_config
            apply_config(user, {"telegram": {"enabled": True, "bot_token": "test-secret-value", "chat_id": "1"}})
            db.commit()
            for record in db.scalars(select(SyncRecord)).all():
                self.assertNotIn("test-secret-value", record.payload)
        config = next(c for c in reversed(self.changes()["changes"]) if c["kind"] == "notification-config")
        self.assertEqual(config["data"]["telegram"]["bot_token"], "test-secret-value")
        result = self.push([{'op_id': 'secret-config', 'kind': 'notification-config', 'id': config['id'], 'base_version': config['version'], 'data': config['data']}])
        self.assertEqual(result.json()['results'][0]['status'], 'applied')
        with Session(self.engine) as db:
            for model in (SyncRecord, SyncChange, SyncReceipt):
                for row in db.scalars(select(model)).all():
                    self.assertNotIn('test-secret-value', row.payload)

    def test_pagination_does_not_skip_changes(self):
        for i in range(3):
            self.create_web(f"item-{i}")
        cursor, seen = 0, []
        while True:
            page = self.changes(cursor, 1)
            seen.extend(c["seq"] for c in page["changes"])
            cursor = page["next_cursor"]
            if not page["has_more"]:
                break
        self.assertEqual(seen, sorted(set(seen)))
        self.assertEqual(len(seen), len(self.changes()["changes"]))

    def test_backup_keeps_risk_fields_and_replace_invalidates_old_epoch(self):
        self.create_web()
        exported = self.client.get('/api/backup/export', headers=self.headers).json()
        self.assertEqual(exported['subscriptions'][0]['trial_end'], '2026-12-01')
        self.assertEqual(exported['subscriptions'][0]['card_last4'], '1234')
        self.assertIn('notify_settings', exported['user'])
        response = self.client.post('/api/backup/import', json={'data': exported, 'replace': True}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get('/api/sync/v1/changes', params={'epoch': self.cap['epoch']}, headers=self.headers).status_code, 409)
        self.assertEqual(self.push([]).status_code, 409)
        with Session(self.engine) as db:
            rows = db.scalars(select(Subscription)).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(str(rows[0].trial_end), '2026-12-01')

    def test_invalid_operation_does_not_rollback_other_operations_or_skip_cursor(self):
        result = self.push([
            {'op_id': 'empty', 'kind': 'categories', 'id': '11111111-1111-4111-8111-111111111111', 'base_version': 0, 'data': {'name': ''}},
            {'op_id': 'good', 'kind': 'categories', 'id': '22222222-2222-4222-8222-222222222222', 'base_version': 0, 'data': {'name': 'Created'}},
        ])
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual([r['status'] for r in result.json()['results']], ['rejected', 'applied'])
        with Session(self.engine) as db:
            self.assertEqual(len(db.scalars(select(Category)).all()), 1)
        self.assertEqual(self.changes()['changes'][-1]['data']['name'], 'Created')

    def test_icon_download_requires_owned_record_and_stays_inside_icon_directory(self):
        web = self.create_web()
        self.client.put(f'/api/subscriptions/{web["id"]}', json={'icon': '/static/icons/fixture.png'}, headers=self.headers)
        record = next(c for c in reversed(self.changes()['changes']) if c['kind'] == 'subscriptions')
        with TemporaryDirectory() as root:
            directory = Path(root) / 'data/icons'; directory.mkdir(parents=True)
            (directory / 'fixture.png').write_bytes(b'icon-fixture')
            with patch('app.routers.sync.Path', side_effect=lambda value: Path(root) / value):
                endpoint = '/api/sync/v1/icons/' + record['id']
                self.assertEqual(self.client.get(endpoint, headers=self.headers).content, b'icon-fixture')
                self.assertEqual(self.client.get(endpoint, headers=self.other_headers).status_code, 404)
                self.client.put(f'/api/subscriptions/{web["id"]}', json={'icon': '/static/icons/../../outside.png'}, headers=self.headers)
                self.assertEqual(self.client.get(endpoint, headers=self.headers).status_code, 404)

    def test_long_existing_notes_survive_encrypted_journal_and_receipt(self):
        response = self.client.post('/api/subscriptions', json={'name': 'Long notes', 'notes': 'x' * 50000}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text[:200])
        record = next(c for c in self.changes()['changes'] if c['kind'] == 'subscriptions')
        self.assertEqual(len(record['data']['notes']), 50000)
        result = self.push([{'op_id': 'long-notes', 'kind': 'subscriptions', 'id': record['id'], 'base_version': record['version'], 'data': record['data']}])
        self.assertEqual(result.json()['results'][0]['status'], 'applied')
        with Session(self.engine) as db:
            self.assertGreater(len(db.get(SyncRecord, record['id']).payload), 65535)
            self.assertGreater(len(db.get(SyncReceipt, (1, 'device-a', 'long-notes')).payload), 65535)


if __name__ == "__main__":
    unittest.main()
