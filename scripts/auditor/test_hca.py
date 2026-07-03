#!/usr/bin/env python3
"""Unit tests for hca — backend mocked, verdict logic and fail-closed paths."""
import importlib.machinery
import importlib.util
import os
import tempfile
import unittest
from unittest import mock

loader = importlib.machinery.SourceFileLoader(
    "hca", os.path.join(os.path.dirname(os.path.abspath(__file__)), "hca"))
spec = importlib.util.spec_from_loader("hca", loader)
hca = importlib.util.module_from_spec(spec)
loader.exec_module(hca)


class TestFileEnv(unittest.TestCase):
    """Covers the shared config loader (same code in hca/hcd/daemon)."""

    def test_process_env_beats_file(self):
        with mock.patch.dict(hca.os.environ, {"HCA_TIMEOUT_S": "42"}), \
             mock.patch.object(hca, "_DICT_FILE_ENV", {"HCA_TIMEOUT_S": "99"}):
            self.assertEqual(hca.fn_env("HCA_TIMEOUT_S"), "42")

    def test_file_fills_gap(self):
        with mock.patch.object(hca, "_DICT_FILE_ENV", {"HCA_AUDITOR_MODEL": "other"}):
            hca.os.environ.pop("HCA_AUDITOR_MODEL", None)
            self.assertEqual(hca.fn_env("HCA_AUDITOR_MODEL", "x"), "other")

    def test_default_when_absent_everywhere(self):
        with mock.patch.object(hca, "_DICT_FILE_ENV", {}):
            self.assertEqual(hca.fn_env("HCR_NOPE", "fallback"), "fallback")

    def test_loader_parses_quotes_comments_blanks(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".config", "holocortex"))
            with open(os.path.join(d, ".config", "holocortex", "env"), "w") as f:
                f.write('# comment\n\nHCR_PORT="9999"\nBAD LINE\nHCR_X=\'y\'\n'
                        'HCR_Y=val   # trailing comment\n')
            with mock.patch.dict(hca.os.environ, {"HOME": d}):
                dict_env = hca.fn_load_file_env()
        self.assertEqual(dict_env, {"HCR_PORT": "9999", "HCR_X": "y",
                                    "HCR_Y": "val"})


class TestVerdictParse(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(hca.fn_parse_verdict("VERDICT: PASS\nlooks fine"),
                         ("PASS", ""))

    def test_fail_with_rule(self):
        v, d = hca.fn_parse_verdict("VERDICT: FAIL G2 no rollback stated")
        self.assertEqual(v, "FAIL")
        self.assertIn("G2", d)

    def test_verdict_not_on_first_line_still_found(self):
        v, _ = hca.fn_parse_verdict("Preamble waffle.\nVERDICT: PASS\n")
        self.assertEqual(v, "PASS")

    def test_garbage_is_fail_closed(self):
        v, d = hca.fn_parse_verdict("The output seems acceptable to me.")
        self.assertEqual(v, "FAIL")
        self.assertIn("fail-closed", d)

    def test_case_insensitive(self):
        self.assertEqual(hca.fn_parse_verdict("verdict: pass")[0], "PASS")


class TestCaptureAppend(unittest.TestCase):
    def test_appends_block(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("# Capture — x\n")
            file_cap = f.name
        try:
            hca.fn_append_capture(file_cap, "FAIL", "G5 key present",
                                  "VERDICT: FAIL G5 key present\nrationale", "gemma4")
            str_body = open(file_cap).read()
            self.assertIn("## Audit (hca)", str_body)
            self.assertIn("**Verdict:** FAIL — G5 key present", str_body)
        finally:
            os.unlink(file_cap)


class TestHardening(unittest.TestCase):
    def _main(self, str_response, dict_envset=None, str_output_text="do the thing"):
        with tempfile.TemporaryDirectory() as d:
            file_out = os.path.join(d, "plan.md")
            open(file_out, "w").write(str_output_text)
            file_gr = os.path.join(d, "GUARDRAILS.md")
            open(file_gr, "w").write("G1..G8")
            lst_argv = ["hca", "--scope", "s", "--output-file", file_out,
                        "--guardrails", file_gr]
            self.dict_prompt = {}
            def fake(str_prompt, obj_cfg):
                self.dict_prompt["str_prompt"] = str_prompt
                return str_response
            with mock.patch.dict(hca.os.environ, dict_envset or {}), \
                 mock.patch.object(hca, "fn_ollama", side_effect=fake), \
                 mock.patch.object(hca.sys, "argv", lst_argv):
                return hca.main()

    def test_data_fencing_present(self):
        self.assertEqual(self._main("VERDICT: PASS"), 0)
        str_p = self.dict_prompt["str_prompt"]
        self.assertIn("<<DATA-", str_p)
        self.assertIn("UNTRUSTED", str_p)

    def test_oversize_input_fails_closed_without_model_call(self):
        int_rc = self._main("VERDICT: PASS",
                            dict_envset={"HCA_MAX_AUDIT_CHARS": "200"},
                            str_output_text="x" * 500)
        self.assertEqual(int_rc, 1)                 # FAIL, not error
        self.assertEqual(self.dict_prompt, {})      # model never consulted


class TestMainFlow(unittest.TestCase):
    def _run(self, str_response, lst_extra=None, b_backend_error=False):
        with tempfile.TemporaryDirectory() as d:
            file_out = os.path.join(d, "plan.md")
            open(file_out, "w").write("do the thing")
            file_gr = os.path.join(d, "GUARDRAILS.md")
            open(file_gr, "w").write("G1..G8")
            lst_argv = ["hca", "--scope", "test scope", "--output-file", file_out,
                        "--guardrails", file_gr] + (lst_extra or [])
            side = RuntimeError("backend down") if b_backend_error else None
            with mock.patch.object(hca, "fn_ollama",
                                   side_effect=side,
                                   return_value=str_response), \
                 mock.patch.object(hca.sys, "argv", lst_argv):
                return hca.main()

    def test_pass_exit_0(self):
        self.assertEqual(self._run("VERDICT: PASS\nok"), 0)

    def test_fail_exit_1(self):
        self.assertEqual(self._run("VERDICT: FAIL G3 no dry run"), 1)

    def test_unparseable_exit_1(self):
        self.assertEqual(self._run("hmm, probably fine"), 1)

    def test_backend_error_exit_2(self):
        self.assertEqual(self._run("", b_backend_error=True), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
