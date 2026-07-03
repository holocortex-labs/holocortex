#!/usr/bin/env python3
"""Holocortex router daemon — local-first LLM routing.

Spec: specs/router.md. Stdlib only (ADR-0002). Guard rails: G6 token budget.

Endpoints:
  POST /route   {"str_query": "...", "str_context": "", "b_force_planner": false}
  GET  /health  backend reachability
  GET  /stats   today's budget usage and escalation counts
"""
import json
import os
import re
import signal
import sys
import time
import hashlib
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ANTHROPIC_VERSION = "2023-06-01"

def fn_load_file_env() -> dict:
    """~/.config/holocortex/env — per-host site config, outside the repo.
    Precedence: process env > this file > localhost fallback (never a site name)."""
    file_cfg = os.path.join(os.path.expanduser("~"), ".config", "holocortex", "env")
    dict_env = {}
    try:
        with open(file_cfg, encoding="utf-8") as f:
            for str_line in f:
                str_line = str_line.strip()
                if not str_line or str_line.startswith("#") or "=" not in str_line:
                    continue
                str_k, str_v = str_line.split("=", 1)
                str_v = str_v.split(" #", 1)[0]  # inline comments; values may not contain " #"
                dict_env[str_k.strip()] = str_v.strip().strip('"').strip("'")
    except OSError:
        pass
    return dict_env


_DICT_FILE_ENV = fn_load_file_env()


def fn_env(str_key: str, str_default: str = "") -> str:
    return os.environ.get(str_key, _DICT_FILE_ENV.get(str_key, str_default))

ESCALATION_REASONS = ("complexity", "context", "tooling", "quality")


def fn_cfg() -> dict:
    """Read configuration from environment. Called once at start-up."""
    return {
        "str_ollama_primary": fn_env("HCR_OLLAMA_PRIMARY", "http://127.0.0.1:11434"),
        "str_ollama_fallback": fn_env("HCR_OLLAMA_FALLBACK", ""),  # empty = no fallback
        "str_reflex_model": fn_env("HCR_REFLEX_MODEL", "phi3"),
        "str_planner_model": fn_env("HCR_PLANNER_MODEL", "claude-sonnet-5"),
        "str_anthropic_key": fn_env("HCR_ANTHROPIC_API_KEY", ""),
        "int_budget_day": int(fn_env("HCR_BUDGET_TOKENS_DAY", "200000")),
        "int_reflex_ctx_chars": int(fn_env("HCR_REFLEX_CTX_CHARS", "12000")),
        "int_complexity_chars": int(fn_env("HCR_COMPLEXITY_CHARS", "1500")),
        "str_tooling_keywords": os.environ.get(
            "HCR_TOOLING_KEYWORDS",
            "mcp,netbox,wake-on-lan,wol,container,jira,confluence,home assistant"),
        "file_log": fn_env("HCR_LOG_FILE", "/data/routing.jsonl"),
        "int_port": int(fn_env("HCR_PORT", "8377")),
        "int_timeout_s": int(fn_env("HCR_TIMEOUT_S", "120")),
    }


CFG = fn_cfg()
LOCK = threading.Lock()

REFLEX_INSTRUCTION = (
    "You are the reflex tier of a local-first LLM router. Answer the query "
    "directly and concisely. If the query is beyond your capability — deep "
    "multi-step reasoning, large design work, or anything you cannot answer "
    "reliably — reply with EXACTLY one line and nothing else:\n"
    "ESCALATE: <reason>\n"
    "where <reason> is one of: complexity, quality.\n\n"
)


# ---------------------------------------------------------------- transport
def fn_post_json(str_url: str, obj_body: dict, dict_headers: dict | None = None,
                 int_timeout: int | None = None) -> dict:
    """POST JSON, return parsed JSON response. Raises on transport error."""
    req = urllib.request.Request(
        str_url, data=json.dumps(obj_body).encode(),
        headers={"Content-Type": "application/json", **(dict_headers or {})},
        method="POST")
    with urllib.request.urlopen(req, timeout=int_timeout or CFG["int_timeout_s"]) as resp:
        return json.loads(resp.read().decode())


def fn_get(str_url: str, int_timeout: int = 5) -> bool:
    try:
        with urllib.request.urlopen(str_url, timeout=int_timeout):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------- backends
def fn_ollama_generate(str_prompt: str) -> str:
    """Reflex generation: primary (GPU host) then fallback (CPU host), empty skipped."""
    obj_body = {"model": CFG["str_reflex_model"], "prompt": str_prompt,
                "stream": False}
    lst_errors = []
    for str_base in (CFG["str_ollama_primary"], CFG["str_ollama_fallback"]):
        if not str_base:
            continue
        try:
            return fn_post_json(f"{str_base}/api/generate", obj_body)["response"]
        except urllib.error.HTTPError as exc:
            str_detail = ""
            try:
                str_detail = json.loads(exc.read().decode()).get("error", "")
            except Exception:
                pass
            lst_errors.append(f"{str_base}: HTTP {exc.code} {str_detail}".strip())
        except Exception as exc:
            lst_errors.append(f"{str_base}: {exc}")
    raise RuntimeError("reflex failed — " + " | ".join(lst_errors))


class PlannerBackend:
    """Interface. v0.3 adds an OpenAI implementation (ADR-0002)."""

    def generate(self, str_prompt: str) -> tuple[str, int]:
        """Return (answer, cloud tokens spent)."""
        raise NotImplementedError


class AnthropicBackend(PlannerBackend):
    def generate(self, str_prompt: str) -> tuple[str, int]:
        if not CFG["str_anthropic_key"]:
            raise RuntimeError("HCR_ANTHROPIC_API_KEY not set")
        obj_resp = fn_post_json(
            "https://api.anthropic.com/v1/messages",
            {"model": CFG["str_planner_model"], "max_tokens": 4096,
             "messages": [{"role": "user", "content": str_prompt}]},
            {"x-api-key": CFG["str_anthropic_key"],
             "anthropic-version": ANTHROPIC_VERSION})
        str_text = "".join(b.get("text", "") for b in obj_resp.get("content", []))
        obj_usage = obj_resp.get("usage", {})
        int_tokens = int(obj_usage.get("input_tokens", 0)) + \
            int(obj_usage.get("output_tokens", 0))
        return str_text, int_tokens


PLANNER: PlannerBackend = AnthropicBackend()


# ---------------------------------------------------------------- policy
def fn_heuristic(str_query: str, str_context: str) -> str | None:
    """Pre-reflex escalation check. Returns a closed-set reason or None."""
    if len(str_context) > CFG["int_reflex_ctx_chars"]:
        return "context"
    lst_kw = [s.strip().lower() for s in CFG["str_tooling_keywords"].split(",") if s.strip()]
    str_q = str_query.lower()
    if any(re.search(r"\b" + re.escape(kw) + r"\b", str_q) for kw in lst_kw):
        return "tooling"
    if len(str_query) > CFG["int_complexity_chars"] or "```" in str_query:
        return "complexity"
    return None


def fn_parse_escalation(str_answer: str) -> str | None:
    """Detect a reflex self-escalation line. Unknown reasons map to 'quality'."""
    m = re.match(r"^\s*ESCALATE:\s*(\w+)\s*$", str_answer.strip(), re.IGNORECASE)
    if not m:
        return None
    str_reason = m.group(1).lower()
    return str_reason if str_reason in ESCALATION_REASONS else "quality"


# ---------------------------------------------------------------- budget/log
def fn_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def fn_budget_spent_today(file_log: str) -> int:
    int_sum = 0
    try:
        with open(file_log, encoding="utf-8") as f:
            for str_line in f:
                try:
                    obj = json.loads(str_line)
                except json.JSONDecodeError:
                    continue
                if obj.get("str_date") == fn_today():
                    int_sum += int(obj.get("int_tokens_cloud", 0))
    except FileNotFoundError:
        pass
    return int_sum


def fn_log(obj_entry: dict) -> None:
    obj_entry["str_date"] = fn_today()
    obj_entry["str_ts"] = datetime.now(timezone.utc).isoformat()
    with LOCK:
        os.makedirs(os.path.dirname(CFG["file_log"]) or ".", exist_ok=True)
        with open(CFG["file_log"], "a", encoding="utf-8") as f:
            f.write(json.dumps(obj_entry) + "\n")


# ---------------------------------------------------------------- routing
def fn_route(str_query: str, str_context: str = "",
             b_force_planner: bool = False) -> dict:
    """Route one query. Deterministic given inputs, policy version, and budget state."""
    t0 = time.monotonic()
    str_hash = hashlib.sha256(str_query.encode()).hexdigest()[:12]
    int_spent = fn_budget_spent_today(CFG["file_log"])
    int_budget = CFG["int_budget_day"]
    b_warn = int_spent >= int_budget * 0.8
    b_exhausted = int_spent >= int_budget

    str_reason = "override" if b_force_planner else fn_heuristic(str_query, str_context)
    str_tier, str_answer, int_tokens = "reflex", "", 0

    if str_reason is None:
        # reflex answers or self-escalates
        str_prompt = REFLEX_INSTRUCTION + \
            (f"Context:\n{str_context}\n\n" if str_context else "") + \
            f"Query:\n{str_query}"
        str_answer = fn_ollama_generate(str_prompt)
        str_reason = fn_parse_escalation(str_answer)

    if str_reason is not None:
        b_override = str_reason == "override"
        if b_exhausted and not b_override:
            # G6: budget gone — reflex-only with refusal note
            str_prompt = (f"Context:\n{str_context}\n\n" if str_context else "") + \
                f"Query:\n{str_query}"
            str_answer = fn_ollama_generate(str_prompt)
            str_answer += ("\n\n[router] daily cloud budget exhausted "
                           f"({int_spent}/{int_budget} tokens); reflex-only answer. "
                           "Override with b_force_planner.")
            str_tier, str_reason = "reflex", f"budget_refusal:{str_reason}"
        else:
            str_prompt = (f"Context:\n{str_context}\n\n" if str_context else "") + \
                str_query
            str_answer, int_tokens = PLANNER.generate(str_prompt)
            str_tier = "planner"

    obj_result = {
        "str_tier": str_tier,
        "str_answer": str_answer,
        "str_reason": str_reason or "reflex_direct",
        "int_tokens_cloud": int_tokens,
        "b_budget_warn": b_warn,
    }
    fn_log({"str_hash": str_hash, "str_tier": str_tier,
            "str_reason": obj_result["str_reason"],
            "int_tokens_cloud": int_tokens,
            "int_ms": int((time.monotonic() - t0) * 1000),
            "b_override": b_force_planner})
    return obj_result


# ---------------------------------------------------------------- http
class Handler(BaseHTTPRequestHandler):
    def _send(self, int_code: int, obj: dict) -> None:
        bs = json.dumps(obj, indent=2).encode()
        self.send_response(int_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(bs)))
        self.end_headers()
        self.wfile.write(bs)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {
                "b_ok": True,
                "b_reflex_primary": fn_get(CFG["str_ollama_primary"] + "/api/tags"),
                "b_reflex_fallback": bool(CFG["str_ollama_fallback"]) and fn_get(CFG["str_ollama_fallback"] + "/api/tags"),
                "b_planner_configured": bool(CFG["str_anthropic_key"]),
            })
        elif self.path == "/stats":
            int_spent = fn_budget_spent_today(CFG["file_log"])
            self._send(200, {
                "str_date": fn_today(),
                "int_tokens_cloud_today": int_spent,
                "int_budget_day": CFG["int_budget_day"],
                "b_budget_warn": int_spent >= CFG["int_budget_day"] * 0.8,
            })
        else:
            self._send(404, {"str_error": "unknown path"})

    def do_POST(self):
        if self.path != "/route":
            self._send(404, {"str_error": "unknown path"})
            return
        try:
            obj_req = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", 0))))
            obj_res = fn_route(
                obj_req["str_query"],
                obj_req.get("str_context", ""),
                bool(obj_req.get("b_force_planner", False)))
            self._send(200, obj_res)
        except KeyError:
            self._send(400, {"str_error": "str_query required"})
        except Exception as exc:  # noqa: BLE001 — surface, don't crash the daemon
            self._send(502, {"str_error": str(exc)})

    def log_message(self, *_):  # quiet — routing log is the record
        pass


def main() -> None:
    srv = ThreadingHTTPServer(("0.0.0.0", CFG["int_port"]), Handler)
    # PID 1 in a container gets no default signal dispositions — without this,
    # `docker stop` waits 10s then SIGKILLs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    print(f"holocortex-router listening on :{CFG['int_port']} "
          f"(budget {CFG['int_budget_day']} tokens/day)")
    srv.serve_forever()


if __name__ == "__main__":
    main()