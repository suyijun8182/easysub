import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch, Mock

import httpcore
import httpx

from app import outbound


class OutboundTests(unittest.TestCase):
    def test_special_addresses_are_blocked_without_a_matching_port_whitelist(self):
        with patch.object(outbound.settings, 'outbound_private_allowlist', ''):
            for host in ['127.0.0.1', '10.0.0.1', '169.254.169.254', '::1', '::ffff:127.0.0.1', '224.0.0.1']:
                with self.subTest(host=host), self.assertRaises(ValueError):
                    outbound.addresses(host, 8000)
        with patch.object(outbound.settings, 'outbound_private_allowlist', '127.0.0.1:8000'):
            self.assertEqual(outbound.addresses('127.0.0.1', 8000), ['127.0.0.1'])
            with self.assertRaises(ValueError):
                outbound.addresses('127.0.0.1', 8001)

    def test_mixed_public_private_dns_answers_are_rejected(self):
        rows = [(2, 1, 6, '', ('8.8.8.8', 443)), (2, 1, 6, '', ('127.0.0.1', 443))]
        with patch.object(outbound.socket, 'getaddrinfo', return_value=rows), self.assertRaises(ValueError):
            outbound.validate_url('https://mixed.example/path')

    def test_connection_uses_checked_numeric_address_not_a_second_hostname_lookup(self):
        rows = [(2, 1, 6, '', ('8.8.8.8', 443))]
        with patch.object(outbound.socket, 'getaddrinfo', return_value=rows) as resolve, patch.object(httpcore.SyncBackend, 'connect_tcp') as connect:
            outbound.PinnedBackend().connect_tcp('public.example', 443, timeout=2)
            resolve.assert_called_once()
            self.assertEqual(connect.call_args.args[:2], ('8.8.8.8', 443))

    def test_redirect_is_rechecked_before_second_request(self):
        def reply(request):
            return httpx.Response(302, headers={'Location': 'http://127.0.0.1:8000/internal'}, request=request)
        with patch.object(outbound.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('8.8.8.8', 443))]), patch.object(httpx.HTTPTransport, 'handle_request', side_effect=reply) as send:
            with outbound.client(follow_redirects=True) as client, self.assertRaises(ValueError):
                client.get('https://public.example/')
            self.assertEqual(send.call_count, 1)

    def test_local_http_transport_works_only_after_administrator_allowlisting(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.end_headers(); self.wfile.write(b'checked transport')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            port = server.server_port
            with patch.object(outbound.settings, 'outbound_private_allowlist', f'127.0.0.1:{port}'), outbound.client() as client:
                self.assertEqual(client.get(f'http://127.0.0.1:{port}').text, 'checked transport')
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_proxy_requires_both_proxy_and_destination_origin_approval(self):
        with patch.object(outbound.settings, 'outbound_private_allowlist', '127.0.0.1:7890'), patch.object(outbound.socket, 'getaddrinfo', return_value=[(2, 1, 6, '', ('8.8.8.8', 443))]):
            with outbound.client(proxy='http://127.0.0.1:7890') as client, self.assertRaises(ValueError):
                client.get('https://public.example')

    def test_credentials_and_non_http_urls_are_rejected(self):
        for value in ['file:///etc/passwd', 'http://user:password@example.com/']:
            with self.subTest(url=value), self.assertRaises(ValueError):
                outbound.validate_url(value)
