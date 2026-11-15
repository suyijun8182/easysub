import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import setup


class SetupSafetyTests(unittest.TestCase):
    def test_configured_system_rejects_connection_probe_without_network_access(self):
        app = FastAPI()
        app.include_router(setup.router)
        with TestClient(app) as client, patch.object(setup.database, 'is_configured', return_value=True), patch.object(setup.bootstrap, 'test_connection', return_value=(True, 'ok')) as connect:
            response = client.post('/api/setup/test', json={
                'host': '127.0.0.1', 'port': 3306, 'user': 'probe', 'database': 'probe'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], '系统已完成数据库配置')
        connect.assert_not_called()

    def test_unconfigured_system_can_still_test_connection(self):
        app = FastAPI()
        app.include_router(setup.router)
        with TestClient(app) as client, patch.object(setup.database, 'is_configured', return_value=False), patch.object(setup.bootstrap, 'test_connection', return_value=(True, 'ok')) as connect:
            response = client.post('/api/setup/test', json={'host': 'mysql.example', 'user': 'user', 'database': 'db'})
        self.assertEqual(response.status_code, 200)
        connect.assert_called_once()
