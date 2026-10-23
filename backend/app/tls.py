"""TLS trust for OIDC: system roots plus an optional deployment CA."""
import os
import ssl


def oidc_ssl_context():
    context = ssl.create_default_context()
    ca_file = os.getenv('OIDC_CA_FILE')
    if ca_file:
        context.load_verify_locations(cafile=ca_file)
    return context
