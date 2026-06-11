import unittest

from termuxdesk.tunnel import _TUNNEL_URL


class TunnelTests(unittest.TestCase):
    def test_quick_tunnel_url_is_extracted_from_cloudflared_output(self):
        line = "INF +-------------------------------- https://demo-name.trycloudflare.com"
        match = _TUNNEL_URL.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(0), "https://demo-name.trycloudflare.com")


if __name__ == "__main__":
    unittest.main()
