import unittest
from unittest.mock import patch

from termuxdesk.cli import build_parser, main


class CliTests(unittest.TestCase):
    def test_start_arguments(self):
        args = build_parser().parse_args(
            ["start", "--host", "0.0.0.0", "--port", "9000", "--tunnel"]
        )
        self.assertEqual(args.host, "0.0.0.0")
        self.assertEqual(args.port, 9000)
        self.assertTrue(args.tunnel)

    def test_missing_display_is_actionable(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("sys.stderr") as stderr:
                self.assertEqual(main(["start"]), 1)
        self.assertIn("DISPLAY is not set", "".join(call.args[0] for call in stderr.write.call_args_list))


if __name__ == "__main__":
    unittest.main()
