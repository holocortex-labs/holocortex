#!/usr/bin/env python3
"""Unit tests for hcr-report — path resolution and summary logic.

The symlink test exists because the v0.6 symlink<->auto-locate seam bug
recurred here in 2026-07 after being fixed in hca/hcd: abspath(__file__)
through a ~/.local/bin symlink pointed the default log at
~/.local/bin/data/. Testing discipline: the bug class gets a test wherever
the auto-locate pattern lives, not only where it first bit.
"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

str_here = os.path.dirname(os.path.abspath(__file__))
str_script = os.path.join(str_here, "hcr-report")


def fn_load(str_path, str_name):
    loader = importlib.machinery.SourceFileLoader(str_name, str_path)
    spec = importlib.util.spec_from_loader(str_name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


hcr_report = fn_load(str_script, "hcr_report")


class TestDefaultLogPath(unittest.TestCase):
    def test_env_wins(self):
        with mock.patch.dict(os.environ, {"HCR_LOG_FILE": "/tmp/x.jsonl"}):
            self.assertEqual(hcr_report.fn_default_log(), "/tmp/x.jsonl")

    def test_direct_invocation_resolves_beside_script(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                hcr_report.fn_default_log(),
                os.path.join(str_here, "data", "routing.jsonl"))

    def test_symlink_invocation_resolves_into_repo(self):
        """Load the module through a symlink (the install-clients.sh
        layout); the default must resolve back beside the real script,
        never beside the symlink."""
        with tempfile.TemporaryDirectory() as str_tmp:
            file_link = os.path.join(str_tmp, "hcr-report")
            os.symlink(str_script, file_link)
            mod_linked = fn_load(file_link, "hcr_report_linked")
            with mock.patch.dict(os.environ, {}, clear=True):
                str_default = mod_linked.fn_default_log()
            self.assertEqual(
                str_default, os.path.join(str_here, "data", "routing.jsonl"))
            self.assertNotIn(str_tmp, str_default)


class TestSummarise(unittest.TestCase):
    def fn_entry(self, str_tier="reflex", str_reason="reflex_direct",
                 int_tokens=0):
        return {"str_tier": str_tier, "str_reason": str_reason,
                "int_tokens_cloud": int_tokens, "int_ms": 100,
                "b_override": False,
                "str_date": "2026-07-04",
                "str_ts": datetime.now(timezone.utc).isoformat()}

    def test_reflex_ratio(self):
        lst = [self.fn_entry(), self.fn_entry(),
               self.fn_entry("planner", "complexity", 500)]
        obj = hcr_report.fn_summarise(lst, 7)
        self.assertEqual(obj["int_queries"], 3)
        self.assertAlmostEqual(obj["flt_reflex_ratio"], 0.667, places=3)
        self.assertEqual(obj["int_tokens_cloud"], 500)
        self.assertEqual(obj["dict_escalation_reasons"], {"complexity": 1})

    def test_empty_log_is_not_an_error(self):
        obj = hcr_report.fn_summarise([], 7)
        self.assertEqual(obj["int_queries"], 0)
        self.assertIsNone(obj["flt_reflex_ratio"])


class TestLoad(unittest.TestCase):
    def test_malformed_lines_skipped(self):
        with tempfile.NamedTemporaryFile(
                "w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({
                "str_ts": datetime.now(timezone.utc).isoformat(),
                "str_tier": "reflex"}) + "\n")
            f.write("not json\n")
            f.write("{\"str_tier\": \"no timestamp\"}\n")
            file_log = f.name
        try:
            lst = hcr_report.fn_load(file_log, 7)
            self.assertEqual(len(lst), 1)
        finally:
            os.unlink(file_log)


if __name__ == "__main__":
    unittest.main()