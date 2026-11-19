import os
import tempfile
import unittest

from odyssey_doctor.checks import scan

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def rules(name):
    return scan(os.path.join(FIX, name)).rules_hit()


class TestChecks(unittest.TestCase):
    def test_clean_js_has_no_findings(self):
        self.assertEqual(rules("clean_js"), set())

    def test_clean_py_has_no_findings(self):
        self.assertEqual(rules("clean_py"), set())

    def test_browser_key(self):
        self.assertIn("OD001", rules("browser_key"))

    def test_public_env_prefix(self):
        self.assertIn("OD001", rules("public_env"))

    def test_key_relay_route(self):
        self.assertIn("OD009", rules("key_relay"))

    def test_no_timeout_handling(self):
        r = rules("no_timeout")
        self.assertIn("OD003", r)
        self.assertNotIn("OD004", r)

    def test_generic_error_handler_is_not_enough(self):
        # no_disconnect has onStreamError but never checks for session_timeout
        self.assertIn("OD003", rules("no_disconnect") | rules("no_cleanup"))

    def test_connect_without_disconnect(self):
        self.assertIn("OD004", rules("no_disconnect"))

    def test_disconnect_without_exit_cleanup(self):
        self.assertIn("OD005", rules("no_cleanup"))

    def test_react_hook_counts_as_cleanup(self):
        r = rules("hook_only")
        self.assertNotIn("OD004", r)
        self.assertNotIn("OD005", r)

    def test_wrong_pip_package(self):
        self.assertIn("OD007", rules("wrong_pip"))

    def test_credentials_then_connect(self):
        self.assertIn("OD008", rules("creds_reconnect"))

    def test_literal_key_is_flagged_and_never_echoed(self):
        fake = "ody_" + "Q" * 6 + "1" * 6 + "z" * 8  # built at runtime, not a real key
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "server.js"), "w") as fh:
                fh.write("const { Odyssey } = require('@odysseyml/odyssey');\n"
                         f"const c = new Odyssey({{ apiKey: '{fake}' }});\n")
            rep = scan(d)
        hits = [f for f in rep.findings if f.rule == "OD002"]
        self.assertEqual(len(hits), 1)
        self.assertNotIn(fake, hits[0].detail)

    def test_placeholder_key_is_not_flagged(self):
        self.assertNotIn("OD002", rules("browser_key"))

    def test_key_returned_inside_object(self):
        found = [f for f in scan(os.path.join(FIX, "key_relay_object")).findings if f.rule == "OD009"]
        self.assertEqual([f.path for f in found], [os.path.join("server", "services", "videoService.js")])

    def test_unrelated_unmount_cleanup_does_not_count(self):
        self.assertIn("OD005", rules("unrelated_cleanup"))

    def test_python_client_built_through_a_factory(self):
        self.assertIn("OD003", rules("py_factory"))

    def test_unrelated_odyssey_python_project_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "agent.py"), "w") as fh:
                fh.write("from odyssey import Odyssey\nagent = Odyssey(env='minecraft')\n")
            rep = scan(d)
        self.assertFalse(rep.uses_sdk)


if __name__ == "__main__":
    unittest.main()
