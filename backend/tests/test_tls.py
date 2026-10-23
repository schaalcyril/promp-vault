import ssl
import pytest
from app.tls import oidc_ssl_context


def test_system_trust_keeps_verification(monkeypatch):
    monkeypatch.delenv('OIDC_CA_FILE', raising=False)
    context = oidc_ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname


def test_missing_configured_ca_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv('OIDC_CA_FILE', str(tmp_path / 'missing.crt'))
    with pytest.raises(OSError):
        oidc_ssl_context()


def test_invalid_ca_fails_closed(monkeypatch, tmp_path):
    path = tmp_path / 'invalid.crt'
    path.write_text('not a certificate')
    monkeypatch.setenv('OIDC_CA_FILE', str(path))
    with pytest.raises(ssl.SSLError):
        oidc_ssl_context()
