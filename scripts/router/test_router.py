#!/usr/bin/env python3
"""Unit tests for holocortex_router — stdlib unittest, backends mocked."""
import json
import os
import tempfile
import unittest
from unittest import mock

import holocortex_router as hr


class FakePlanner(hr.PlannerBackend):
    def __init__(self, str_answer="planner-answer", int_tokens=500):
        self.str_answer, self.int_tokens = str_answer, int_tokens
        self.int_calls = 0

    def generate(self, str_prompt):
        self.int_calls += 1
        return self.str_answer, self.int_tokens


class TestHeuristic(unittest.TestCase):
    def test_plain_query_stays_local(self):
        self.assertIsNone(hr.fn_heuristic("what is the capital of France", ""))

    def test_large_context_escalates(self):
        self.assertEqual(
            hr.fn_heuristic("summarise", "x" * (hr.CFG["int_reflex_ctx_chars"] + 1)),
            "context")

    def test_tooling_keyword_escalates(self):
        self.assertEqual(hr.fn_heuristic("query netbox for the hypervisor's IPs", ""), "tooling")

    def test_long_query_is_complexity(self):
        self.assertEqual(hr.fn_heuristic("y" * 2000, ""), "complexity")

    def test_code_fence_is_complexity(self):
        self.assertEqual(hr.fn_heuristic("review this ```code```", ""), "complexity")


class TestEscalationParse(unittest.TestCase):
    def test_valid_reason(self):
        self.assertEqual(hr.fn_parse_escalation("ESCALATE: complexity"), "complexity")

    def test_unknown_reason_maps_to_quality(self):
        self.assertEqual(hr.fn_parse_escalation("ESCALATE: vibes"), "quality")

    def test_normal_answer_is_none(self):
        self.assertIsNone(hr.fn_parse_escalation("Paris."))


class TestBudget(unittest.TestCase):
    def test_sums_only_today(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"str_date": hr.fn_today(), "int_tokens_cloud": 100}) + "\n")
            f.write(json.dumps({"str_date": "2020-01-01", "int_tokens_cloud": 999}) + "\n")
            f.write("not-json\n")
            file_log = f.name
        try:
            self.assertEqual(hr.fn_budget_spent_today(file_log), 100)
        finally:
            os.unlink(file_log)

    def test_missing_file_is_zero(self):
        self.assertEqual(hr.fn_budget_spent_today("/nonexistent/x.jsonl"), 0)


class TestRoute(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        hr.CFG["file_log"] = os.path.join(self.tmp.name, "routing.jsonl")
        self.planner = FakePlanner()
        self._orig_planner = hr.PLANNER
        hr.PLANNER = self.planner

    def tearDown(self):
        hr.PLANNER = self._orig_planner
        self.tmp.cleanup()

    def _log_lines(self):
        with open(hr.CFG["file_log"], encoding="utf-8") as f:
            return [json.loads(l) for l in f]

    def test_reflex_direct(self):
        with mock.patch.object(hr, "fn_ollama_generate", return_value="Paris."):
            obj = hr.fn_route("capital of France?")
        self.assertEqual(obj["str_tier"], "reflex")
        self.assertEqual(obj["str_reason"], "reflex_direct")
        self.assertEqual(obj["int_tokens_cloud"], 0)
        self.assertEqual(self.planner.int_calls, 0)
        self.assertEqual(self._log_lines()[0]["str_tier"], "reflex")

    def test_reflex_self_escalation_reaches_planner(self):
        with mock.patch.object(hr, "fn_ollama_generate",
                               return_value="ESCALATE: complexity"):
            obj = hr.fn_route("design a distributed thing")
        self.assertEqual(obj["str_tier"], "planner")
        self.assertEqual(obj["str_reason"], "complexity")
        self.assertEqual(obj["int_tokens_cloud"], 500)

    def test_heuristic_escalation_skips_reflex(self):
        with mock.patch.object(hr, "fn_ollama_generate") as m:
            obj = hr.fn_route("wake the hypervisor via wol")
            m.assert_not_called()
        self.assertEqual(obj["str_reason"], "tooling")
        self.assertEqual(obj["str_tier"], "planner")

    def test_budget_exhausted_refuses_planner(self):
        hr.fn_log({"int_tokens_cloud": hr.CFG["int_budget_day"]})
        with mock.patch.object(hr, "fn_ollama_generate", return_value="local best effort"):
            obj = hr.fn_route("query netbox please")
        self.assertEqual(obj["str_tier"], "reflex")
        self.assertTrue(obj["str_reason"].startswith("budget_refusal:"))
        self.assertIn("budget exhausted", obj["str_answer"])
        self.assertEqual(self.planner.int_calls, 0)

    def test_force_planner_overrides_exhausted_budget(self):
        hr.fn_log({"int_tokens_cloud": hr.CFG["int_budget_day"]})
        obj = hr.fn_route("anything", b_force_planner=True)
        self.assertEqual(obj["str_tier"], "planner")
        self.assertEqual(obj["str_reason"], "override")
        self.assertEqual(self.planner.int_calls, 1)
        self.assertTrue(self._log_lines()[-1]["b_override"])

    def test_warn_flag_at_80_percent(self):
        hr.fn_log({"int_tokens_cloud": int(hr.CFG["int_budget_day"] * 0.85)})
        with mock.patch.object(hr, "fn_ollama_generate", return_value="ok"):
            obj = hr.fn_route("small question")
        self.assertTrue(obj["b_budget_warn"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
