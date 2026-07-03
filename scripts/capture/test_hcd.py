#!/usr/bin/env python3
"""Tests for hcd — model mocked, filesystem behaviour verified."""
import importlib.machinery
import importlib.util
import os
import tempfile
import unittest
from unittest import mock

str_here = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("hcd", os.path.join(str_here, "hcd"))
spec = importlib.util.spec_from_loader("hcd", loader)
hcd = importlib.util.module_from_spec(spec)
loader.exec_module(hcd)

STR_FAKE_DRAFT = "# Capture — x\n\n## Context\nTest context.\n"


class TestSlug(unittest.TestCase):
    def test_spaces_and_case(self):
        self.assertEqual(hcd.fn_slug("Router Debug Session"), "router-debug-session")

    def test_strips_junk(self):
        self.assertEqual(hcd.fn_slug("  weird//topic!  "), "weird--topic")


class TestMainFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file_notes = os.path.join(self.tmp.name, "notes.txt")
        open(self.file_notes, "w").write("Fixed the thing. Dead end: tried X first.")
        self.str_out = os.path.join(self.tmp.name, "captures")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, lst_extra=None):
        lst_argv = ["hcd", "--topic", "test-topic", "--input", self.file_notes,
                    "--date", "2026-07-02", "--out-dir", self.str_out] + (lst_extra or [])
        with mock.patch.object(hcd, "fn_ollama", return_value=STR_FAKE_DRAFT), \
             mock.patch.object(hcd.sys, "argv", lst_argv):
            return hcd.main()

    def test_writes_draft_with_marker(self):
        self.assertEqual(self._run(), 0)
        file_out = os.path.join(self.str_out, "2026-07-02-test-topic.md.draft")
        self.assertTrue(os.path.exists(file_out))
        str_body = open(file_out).read()
        self.assertIn("DRAFT by hcd/", str_body)
        self.assertIn("rename to .md before commit", str_body)
        self.assertIn("Test context.", str_body)

    def test_refuses_overwrite(self):
        self.assertEqual(self._run(), 0)
        self.assertEqual(self._run(), 2)  # same args again → refuse

    def test_empty_material_errors(self):
        open(self.file_notes, "w").write("   \n")
        self.assertEqual(self._run(), 2)

    def test_backend_down_exit_2(self):
        lst_argv = ["hcd", "--topic", "t", "--input", self.file_notes,
                    "--out-dir", self.str_out]
        with mock.patch.object(hcd, "fn_ollama", side_effect=RuntimeError("down")), \
             mock.patch.object(hcd.sys, "argv", lst_argv):
            self.assertEqual(hcd.main(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
