# Holocortex — System Mind Map

Renders in any Mermaid-aware viewer (GitHub, Obsidian, VS Code).

```mermaid
mindmap
  root((Holocortex))
    Substrate
      Git repo — markdown source of truth
      captures/ — dated knowledge, the growing wiki
      docs/adr/ — immutable decisions
      BACKLOG.md — tracked future work
      Render layer — deferred, backlog
    Model tiers
      Reflex — local, free
        phi3 / qwen via ollama
        the GPU host, fallback the always-on host CPU
        triage, summaries, capture drafts
      Planner — cloud, budgeted
        Claude / GPT-4.1
        design & multi-step reasoning
      Auditor
        fresh context, checks vs GUARDRAILS
        gate before action — G4
    Router
      local-first policy — G6
      closed escalation set
        complexity / context / tooling / quality
      daily token budget + JSONL log
      daemon on the always-on host, mesh-addressed
    MCP layer
      local MCP servers
        journal / netbox / wol / containers / weather
      smoke tests — read-only agent sweep
      drift findings — G8
    Processes
      P1 Capture — every session ends in a file
      P2 Route — reflex first, reasoned escalation
      P3 Audit — never self-audit
      P4 Decide — ADRs, supersede not edit
      P5 Review — weekly 15-min groom
    Guard rails
      read-only default — G1
      reversibility stated — G2
      dry-run first — G3
      no secrets in substrate — G5
      capture mandatory — G7
    Infrastructure
      always-on node — services
      GPU workstation — dev + inference
      hypervisor — secondary DNS
      NAS — backup target
      private mesh VPN
```

## Reading the map

Left half is knowledge flow (substrate ← processes), right half is execution
(tiers ← router ← infra). Guard rails cut across everything. If a node here has
no corresponding file or backlog item, that's drift — G8 applies to the map too.
