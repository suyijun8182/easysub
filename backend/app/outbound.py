"""Checked, pinned outbound connections for user-controlled notification targets.

HTTPX 0.28.1 / HTTPCore 1.0.9: keep the original HTTP Host and TLS SNI while
the network backend connects only to an address checked for this connection.
"""
import ipaddress
import socket
import ssl
import smtplib

import httpcore
import httpx

from app.config import settings


def _allowed(host: str, port: int) -> bool:
    target = f"{host.lower().rstrip('.')}:{port}"
    return target in {x.strip().lower().rstrip('.') for x in settings.outbound_private_allowlist.split(',') if x.strip()}


def addresses(host: str, port: int) -> list[str]:
    try:
        resolved = [str(ipaddress.ip_address(host))]
    except ValueError:
        resolved = list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
    if not resolved:
        raise ValueError("通知目标没有可用地址")
    for value in resolved:
        ip = ipaddress.ip_address(value)
        ip = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
        if (not ip.is_global or ip.is_multicast) and not _allowed(host, port) and not _allowed(str(ip), port):
            raise ValueError("目标为本机或内网地址，请由管理员配置 OUTBOUND_PRIVATE_ALLOWLIST")
    return resolved


def validate_url(value: str) -> httpx.URL:
    url = httpx.URL(value)
    if url.scheme not in ('http', 'https') or not url.host or url.username or url.password:
        raise ValueError("通知地址必须为不含登录凭据的 HTTP(S) URL")
    addresses(url.host, url.port or (443 if url.scheme == 'https' else 80))
    return url


class PinnedBackend(httpcore.SyncBackend):
    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        # Resolve once and pass only a numeric IP to the actual connection.
        checked = addresses(host, port)
        return super().connect_tcp(checked[0], port, timeout, local_address, socket_options)


class CheckedTransport(httpx.HTTPTransport):
    def __init__(self, proxy=None):
        super().__init__(trust_env=False)
        self._pool.close()
        self.proxy = proxy
        if proxy:
            url = validate_url(proxy)
            if not _allowed(url.host, url.port or (443 if url.scheme == 'https' else 80)):
                raise ValueError("代理必须由管理员加入 OUTBOUND_PRIVATE_ALLOWLIST")
            self._pool = httpcore.HTTPProxy(proxy_url=str(url), ssl_context=ssl.create_default_context(),
                proxy_ssl_context=ssl.create_default_context() if url.scheme == "https" else None, network_backend=PinnedBackend())
        else:
            self._pool = httpcore.ConnectionPool(ssl_context=ssl.create_default_context(), network_backend=PinnedBackend())

    def handle_request(self, request):
        url = validate_url(str(request.url))
        # A proxy controls destination DNS. Trust it only for administrator-approved
        # destination origins, even when their current DNS answers are public.
        if self.proxy and not _allowed(url.host, url.port or (443 if url.scheme == 'https' else 80)):
            raise ValueError("使用代理时，目标也必须由管理员加入 OUTBOUND_PRIVATE_ALLOWLIST")
        return super().handle_request(request)


def client(timeout=15, proxy=None, follow_redirects=False):
    return httpx.Client(timeout=timeout, transport=CheckedTransport(proxy), trust_env=False,
                        follow_redirects=follow_redirects)


def validate_config(channel: str, conf: dict):
    for key in ('url', 'server', 'api_base', 'proxy', 'proxy_base'):
        value = conf.get(key)
        if value:
            validate_url(value if '://' in value else 'https://' + value)
    for value in conf.get('urls') or []:
        validate_url(value)
    if channel == 'email' and conf.get('host'):
        addresses(conf['host'], int(conf.get('port') or (465 if conf.get('ssl') else 587)))


class CheckedSMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        ip = addresses(host, port)[0]
        return socket.create_connection((ip, port), timeout, self.source_address)


class CheckedSMTPSSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        ip = addresses(host, port)[0]
        sock = socket.create_connection((ip, port), timeout, self.source_address)
        try:
            return self.context.wrap_socket(sock, server_hostname=self._host)
        except Exception:
            sock.close()
            raise


def error_summary(exc: Exception) -> str:
    # Provider exceptions often embed secret-bearing URLs and response bodies.
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}：通知请求失败，请检查渠道配置"
    return f"{type(exc).__name__}：请求失败，请检查地址、白名单或渠道配置"
