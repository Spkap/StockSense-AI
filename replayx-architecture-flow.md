# ReplayX Flow Architecture

This is the simplest walkthrough version of ReplayX based on the actual app. It shows how an incident enters the system, how the orchestrator moves through bounded phases, how the dashboard gets live updates, and how ReplayX preserves reusable incident memory.

```mermaid
flowchart TD
    A[User reports a production-style bug]

    A -->|message in bugs channel| B[Slack Intake Service]
    A -->|or start directly| C[Run API]
    A -->|or use safety net| D[Replay Route]

    subgraph PRODUCT["ReplayX Product Surface"]
        E[Dashboard UI]
        F[Live Run View]
        G[Replay View]
        H[Phase Timeline + Workers]
        I[Diagnosis / Fix / Postmortem Panels]
    end

    B -->|incident text + metadata| C
    C -->|create runId + initial state| J[Dashboard Server]
    D -->|load saved run artifacts| J
    J -->|render page data| E
    E --> F
    E --> G
    F --> H
    F --> I
    G --> H
    G --> I

    subgraph RUNTIME["Live Update Runtime"]
        K[WebSocket Channel]
        L[SSE / Polling Fallback]
        M[Run State Files]
    end

    J --> K
    J --> L
    K --> E
    L --> E
    M --> J

    subgraph ORCH["ReplayX Orchestrator"]
        P1[1. Incident Intake]
        P2[2. Fast-Path Skill Match]
        P3[3. Repro + Environment Verification]
        P4[4. Diagnosis Arena]
        P5[5. Challenger Validation]
        P6[6. Fix Arena]
        P7[7. Review + Regression Plan]
        P8[8. Postmortem + Skill Writing]
    end

    C --> P1
    P1 --> P2
    P2 -->|high-confidence skill match| P8
    P2 -->|no strong match| P3
    P3 --> P4
    P4 --> P5
    P5 --> P6
    P6 --> P7
    P7 --> P8

    subgraph WORKERS["Codex-First Specialist Workers"]
        W1[Diagnosis Workers<br/>concurrency / auth / data-shape / recent-change / database / state-handoff]
        W2[Challenger Worker<br/>tries to falsify the top diagnosis]
        W3[Fix Strategy Workers<br/>minimal / safe / durable]
        W4[Review Worker<br/>approves or vetoes the proposal]
        W5[Skill Writer<br/>captures reusable incident knowledge]
    end

    P4 --> W1
    P5 --> W2
    P6 --> W3
    P7 --> W4
    P8 --> W5

    subgraph TARGET["Incident Context + Target System"]
        T1[Incident Bundle]
        T2[Repo / Suspected Files / Recent Changes]
        T3[demo_app<br/>checkout race / auth refresh / null shape repros]
        T4[Failing Command + Healthy Command]
        T5[Logs / Stack Traces / Metrics]
    end

    P1 --> T1
    P1 --> T5
    P3 --> T2
    P3 --> T3
    P3 --> T4
    P4 --> T1
    P4 --> T2
    P4 --> T5
    P5 --> T1
    P5 --> T2
    P6 --> T2
    P7 --> T4

    subgraph MEMORY["Replay-Safe Artifact Layer"]
        R1[Normalized Incident JSON]
        R2[Per-Phase JSON Outputs]
        R3[Ranked Diagnosis]
        R4[Fix Recommendation]
        R5[Regression Verification Plan]
        R6[Postmortem]
        R7[Reusable Incident Skill]
    end

    P1 --> R1
    P2 --> R2
    P3 --> R2
    P4 --> R3
    P5 --> R3
    P6 --> R4
    P7 --> R5
    P8 --> R6
    P8 --> R7

    R1 --> M
    R2 --> M
    R3 --> M
    R4 --> M
    R5 --> M
    R6 --> M
    R7 --> M

    R7 -->|future similar incidents| P2
```

## Walkthrough

1. A bug is reported in Slack or a run is started directly through the run API.
2. ReplayX creates a live run, persists the run state, and opens the dashboard flow.
3. The dashboard server pushes live progress over WebSockets, with SSE or polling as fallback.
4. The orchestrator moves through a fixed sequence: intake, skill match, repro, diagnosis, challenger, fix arena, review, and postmortem.
5. The diagnosis arena uses bounded Codex-first workers instead of one large opaque agent run.
6. Those workers inspect the incident bundle, repo context, demo app behavior, and verification commands.
7. The challenger tries to falsify weak diagnoses before ReplayX accepts a root cause.
8. The fix arena ranks fix strategies by blast radius and durability rather than patching blindly.
9. Every phase writes machine-readable artifacts so the run is inspectable and replayable.
10. At the end, ReplayX emits not just a diagnosis, but also a verification plan, a postmortem, and a reusable skill for future incidents.
