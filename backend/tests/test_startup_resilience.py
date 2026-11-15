import unittest
from unittest.mock import patch

from app import bootstrap, database
from app.services import scheduler


class StartupResilienceTests(unittest.TestCase):
    def tearDown(self):
        database.reset_engine()

    def test_failed_secret_rotation_does_not_block_database_startup(self):
        # A single unreadable row must not make the app treat the database as unavailable.
        with patch.object(bootstrap, 'config_exists', return_value=True), \
                patch.object(bootstrap, 'load_config', return_value={}), \
                patch.object(bootstrap, 'build_url', return_value='sqlite://'), \
                patch('app.seed.seed_all'), \
                patch.object(scheduler, 'start_scheduler') as start, \
                patch('app.secrets_store.reencrypt_legacy_secrets', side_effect=RuntimeError('bad row')):
            self.assertTrue(database.connect_from_saved_config(force=True))
            self.assertTrue(database.is_configured())
            start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
