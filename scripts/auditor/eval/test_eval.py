#!/usr/bin/env python3
"""Tests for run_eval — oracle and adversarial fake models, no network."""
import importlib.machinery
import importlib.util
import json
import os
import unittest
from unittest import mock

str_here = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("run_eval", os.path.join(str_here, "run_eval"))
spec = importlib.util.spec_from_loader("run_eval", loader)
run_eval = importlib.util.module_from_spec(spec)
loader.exec_module(run_eval)

LST_CASES = [json.loads(l) for l in open(os.path.join(str_here, "cases.jsonl"))]
DICT_EXPECTED = {c["str_output"]: c["str_expected"] for c in LST_CASES}


class TestRunModel(unittest.TestCase):
    def test_oracle_scores_perfect(self):
        def fake(str_prompt, obj_cfg):
            for str_out, str_exp in DICT_EXPECTED.items():
                if str_out in str_prompt:
                    return f"VERDICT: {str_exp}\nreason"
            raise AssertionError("case not found in prompt")
        with mock.patch.object(run_eval.hca, "fn_ollama", side_effect=fake):
            obj = run_eval.fn_run_model("oracle", LST_CASES, "G1..G8")
        self.assertEqual(obj["int_correct"], len(LST_CASES))
        self.assertEqual(obj["int_false_pass"], 0)
        self.assertEqual(obj["int_false_fail"], 0)

    def test_sycophant_counts_false_passes(self):
        with mock.patch.object(run_eval.hca, "fn_ollama",
                               return_value="VERDICT: PASS\nall good"):
            obj = run_eval.fn_run_model("sycophant", LST_CASES, "G1..G8")
        int_should_fail = sum(1 for c in LST_CASES if c["str_expected"] == "FAIL")
        self.assertEqual(obj["int_false_pass"], int_should_fail)

    def test_gibberish_is_fail_closed_no_false_pass(self):
        with mock.patch.object(run_eval.hca, "fn_ollama",
                               return_value="as an ai model i think maybe"):
            obj = run_eval.fn_run_model("gibberish", LST_CASES, "G1..G8")
        self.assertEqual(obj["int_false_pass"], 0)  # fail-closed protects here
        int_should_pass = sum(1 for c in LST_CASES if c["str_expected"] == "PASS")
        self.assertEqual(obj["int_false_fail"], int_should_pass)

    def test_backend_error_not_scored_as_pass(self):
        with mock.patch.object(run_eval.hca, "fn_ollama",
                               side_effect=RuntimeError("down")):
            obj = run_eval.fn_run_model("dead", LST_CASES, "G1..G8")
        self.assertEqual(obj["int_correct"], 0)
        self.assertEqual(obj["int_false_pass"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
