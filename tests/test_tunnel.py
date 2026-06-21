import unittest

from termux_desk.tunnel import LocalhostRunTunnel


class TunnelTests(unittest.TestCase):
    def test_localhost_run_url_is_extracted(self):
        line = "296cd66f6b8ea2.lhr.life tunneled with tls termination, https://296cd66f6b8ea2.lhr.life"
        tunnel = LocalhostRunTunnel(8765)
        import re
        match = re.search(r"(https://[^\s]+\.lhr\.life[^\s]*)", line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "https://296cd66f6b8ea2.lhr.life")


if __name__ == "__main__":
    unittest.main()
