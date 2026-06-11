import asyncio
import os
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import termux_desk
from termux_desk.server import VIEWER_HTML, TermuxDeskError, TermuxDeskServer


class ServerConfigurationTests(unittest.TestCase):
    def test_public_api_imports_without_runtime_dependencies(self):
        self.assertEqual(termux_desk.__version__, "0.1.2")
        self.assertIs(termux_desk.TermuxDeskError, TermuxDeskError)

    def test_contributor_viewer_matches_embedded_viewer(self):
        viewer = Path(termux_desk.__file__).with_name("viewer.html").read_text()
        self.assertEqual(viewer, VIEWER_HTML)

    def test_configuration_validation(self):
        with self.assertRaises(ValueError):
            TermuxDeskServer(port=0)
        with self.assertRaises(ValueError):
            TermuxDeskServer(fps=0)
        with self.assertRaises(ValueError):
            TermuxDeskServer(quality=96)

    def test_start_checks_display_before_importing_dependencies(self):
        with patch.dict(os.environ, {}, clear=True):
            server = TermuxDeskServer(display=None)
            with self.assertRaisesRegex(TermuxDeskError, "DISPLAY is not set"):
                asyncio.run(server.start())

    def test_local_url_uses_loopback_for_wildcard_listener(self):
        self.assertEqual(
            TermuxDeskServer(host="0.0.0.0", display=":0").local_url,
            "http://127.0.0.1:8765",
        )

    def test_normalized_coordinates_are_scaled_and_clamped(self):
        server = TermuxDeskServer(display=":0")
        screen = SimpleNamespace(width_in_pixels=100, height_in_pixels=50)
        server._runtime = SimpleNamespace(
            display=SimpleNamespace(screen=lambda: screen)
        )
        self.assertEqual(server._point({"x": 0.5, "y": 2}), (50, 49))

    @patch.object(TermuxDeskServer, "_run_clipboard")
    def test_clipboard_set_falls_back_to_xsel(self, run_clipboard):
        run_clipboard.side_effect = [FileNotFoundError("xclip"), ""]
        TermuxDeskServer(display=":0")._set_clipboard("hello")
        self.assertEqual(
            run_clipboard.call_args_list[1].args,
            (["xsel", "--clipboard", "--input"], "hello"),
        )

    @patch.object(TermuxDeskServer, "_run_clipboard")
    def test_clipboard_get_falls_back_to_xsel(self, run_clipboard):
        run_clipboard.side_effect = [
            subprocess.CalledProcessError(1, "xclip"),
            "remote text",
        ]
        result = TermuxDeskServer(display=":0")._get_clipboard()
        self.assertEqual(result, "remote text")
        self.assertEqual(
            run_clipboard.call_args_list[1].args,
            (["xsel", "--clipboard", "--output"],),
        )


if __name__ == "__main__":
    unittest.main()
