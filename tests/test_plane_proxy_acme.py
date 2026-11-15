"""T-8 repro (AC-12): plane proxy crash-loops with
'parsing caddyfile tokens for acme_ca: wrong argument count' because compose
sets CERT_ACME_CA to the empty string; the image Caddyfile has
`acme_ca {$CERT_ACME_CA:<letsencrypt default>}` and an empty (set) variable
does not trigger the default. Expected: CERT_ACME_CA is unset or non-empty.
Currently FAILS (live: selfhost-plane-proxy-1 Restarting, :8703 refuses)."""
import os
import re
import unittest

COMPOSE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stacks", "plane", "compose.yaml")


class PlaneProxyAcme(unittest.TestCase):
    def test_cert_acme_ca_not_empty_string(self):
        text = open(COMPOSE).read()
        m = re.search(r'^\s*CERT_ACME_CA:\s*(.*?)\s*$', text, re.M)
        if m is None:
            return  # unset: Caddy default applies
        self.assertNotIn(m.group(1), ('""', "''", ""), "CERT_ACME_CA set to empty string breaks Caddyfile acme_ca")


if __name__ == "__main__":
    unittest.main()
