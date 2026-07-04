# Architecture

Two views of the same system. The **C4 Container diagram** shows the runnable
pieces and how they communicate (the logical software architecture). The
**Deployment diagram** shows which physical host each piece runs on (the
operational topology). Read them together: C4 answers "what talks to what,"
deployment answers "what runs where."

Both render on GitHub and in the mkdocs site. Host labels are role-based by
design — the same architecture applies to any hostnames.

## C4 Container diagram — logical view

```mermaid
C4Container
    title Container diagram — Holocortex

    Person(operator, "Operator", "Works through the CLI tools; reviews and commits")

    System_Boundary(hc, "Holocortex") {
        Container(hcr, "hcr", "bash CLI", "Router client; sends queries, carries auth token")
        Container(hca, "hca", "python CLI", "Auditor gate (P3); fail-closed verdicts")
        Container(hcd, "hcd", "python CLI", "Capture drafter; writes .draft only")
        Container(report, "hcr-report", "python CLI", "Routing-log analysis for the weekly review")
        Container(router, "Router daemon", "python / Docker", "Local-first routing, token budget, JSONL log")
        Container(hook, "pre-commit hook", "bash", "Secret scan + draft-marker gate")
        Container(site, "Render site", "mkdocs / Docker", "Read-only view of the substrate")
        ContainerDb(substrate, "Substrate", "git + markdown", "Captures, ADRs, guard rails, specs, routing log")
    }

    Container_Ext(reflex, "Reflex model", "ollama", "Local, free — primary GPU, optional CPU fallback")
    System_Ext(cloud, "Cloud planner", "Claude / GPT API", "Budgeted; escalation only")

    Rel(operator, hcr, "asks", "CLI")
    Rel(hcr, router, "POST /route", "HTTP + X-HC-Token")
    Rel(router, reflex, "generate", "HTTP/mesh")
    Rel(router, cloud, "escalate (reasoned)", "HTTPS")
    Rel(router, substrate, "appends routing log")
    Rel(hca, reflex, "audit", "HTTP")
    Rel(hcd, reflex, "draft", "HTTP")
    Rel(hcd, substrate, "writes .draft")
    Rel(report, substrate, "reads routing log")
    Rel(operator, substrate, "reviews & commits")
    Rel(hook, substrate, "guards every commit")
    Rel(site, substrate, "renders (read-only)")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

If the C4 renderer is unavailable, the same relationships hold in the
deployment view below.

## Deployment diagram — physical view

The CPU fallback is drawn dashed because it is **optional**. It is a valid
resilience choice, but a deployment may reasonably run without it (see Notes).
When present, it belongs on a host isolated from critical always-on services.

```mermaid
flowchart TB
    operator([Operator])
    cloud{{"Cloud planner API<br/>Claude / GPT — HTTPS"}}

    subgraph gpu["GPU workstation"]
        ollamaP["ollama — primary reflex<br/>gemma4"]
    end

    subgraph always["Always-on host"]
        clients["hcr / hca / hcd / hcr-report"]
        rtr["holocortex-router :8377<br/>auth token"]
        web["mkdocs site :8378"]
        repo[("git substrate<br/>+ routing.jsonl")]
    end

    subgraph iso["Isolated host — optional"]
        ollamaF["ollama — optional CPU fallback :11434<br/>away from critical services"]
    end

    subgraph nas["NAS"]
        bak[("backups")]
    end

    operator --> clients
    clients -->|"HTTP :8377 + token"| rtr
    rtr -->|"mesh"| ollamaP
    rtr -.->|"optional fallback, mesh"| ollamaF
    rtr -->|"escalate"| cloud
    rtr --> repo
    web -. "read-only" .- repo
    clients -. "audit/draft, mesh" .-> ollamaP
    repo -.->|"backup"| bak
    always <-. "private mesh VPN" .-> gpu
    always <-. "mesh" .-> iso

    classDef optional stroke-dasharray:4,opacity:0.55
    class iso,ollamaF optional
```

## Notes

- **Trust boundary** is the private mesh: the router port is reachable across
  it, optionally gated by an auth token. Nodes reach inference by mesh name,
  so the primary GPU host sleeping degrades to the optional fallback (if
  deployed) rather than failing outright.
- **The CPU fallback is optional, and where it runs matters.** It keeps the
  reflex tier alive when the primary GPU host is unavailable — but sustained
  CPU inference is thermally heavy, so it must **not** be co-located with a
  critical always-on service (for example DNS): a redundancy mechanism should
  never be able to take down something more important than what it protects.
  Put it on an isolated or better-cooled host, or omit it entirely. Running
  without a fallback is a legitimate choice when the routing log shows the
  primary's downtime isn't actually costing you — reflex simply returns an
  honest "unavailable" and the cloud planner still works.
- **The substrate is the hub of the logical view for a reason:** every tool
  reads from or writes to git + markdown. That is the design — the repo is the
  system, and services are replaceable views and actors over it.