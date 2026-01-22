# SafeAgent -- Trust Infrastructure for Autonomous AI Code Agents

SafeAgent is a **production-grade execution layer for autonomous AI coding agents** that enforces safety, determinism, and auditability before any code change reaches your repository.

This is not another agent demo. This is **infrastructure for making AI agents safe enough for real production environments**.

------------------------------------------------------------------------

## The Problem

Modern AI coding agents frequently fail in dangerous ways:

-   They hallucinate files that do not exist
-   They misunderstand code context
-   They silently delete critical logic
-   They overwrite working systems
-   They produce diffs that do not apply
-   They bypass safety assumptions

Giving such agents direct write access to production code is **operationally unsafe**.

Most agent demos optimize for **capability**. SafeAgent optimizes for **trust**.

------------------------------------------------------------------------

## The Solution

SafeAgent introduces a **deterministic, auditable, safety-first execution pipeline** between user intent and repository changes.

Execution flow:

User request
→ Repo cloned into isolated workspace
→ File discovery from real filesystem
→ Cryptographic hashing of files (ground truth)
→ LLM selects only existing files
→ LLM proposes patch against real content
→ Policy engine validates intent
→ Diff safety validation
→ Patch applied in sandbox only
→ AST checks executed
→ Tests executed (configurable)
→ Full execution trace recorded
→ Full diff recorded
→ Full audit log stored
→ Only then: GitHub PR created

At no point does the LLM touch the real repository directly.

------------------------------------------------------------------------

## Safety Guarantees

SafeAgent enforces hard constraints:

-   LLM never writes directly to real repos
-   All edits occur inside temporary isolated clones
-   Every file edit is SHA-verified against disk
-   Hallucinated files are automatically rejected
-   Invalid diffs fail safely
-   Self-repair loop handles patch instability
-   Full rewrite fallback ensures robustness
-   Policies can block sensitive paths
-   Tests and AST validation act as guardrails
-   Every run is auditable and replayable

This creates **defense-in-depth for autonomous agents**.

------------------------------------------------------------------------

## Security Model

SafeAgent explicitly assumes the LLM is **untrusted**.

The system is designed so that even a fully adversarial model cannot:

- Modify files that do not exist
- Write to arbitrary paths
- Modify the real repository directly
- Bypass hash validation
- Bypass diff validation
- Skip verification steps
- Push directly to main
- Delete critical files undetected

All safety guarantees are enforced **outside the model**, at the infrastructure layer.

This mirrors how real-world secure systems are designed:
> Never trust the component that is easiest to compromise.

------------------------------------------------------------------------

## Why This Matters

Enterprises want AI agents. They do not trust AI agents.

Security teams, infra teams, and compliance teams require:

-   Determinism
-   Traceability
-   Observability
-   Auditability
-   Control

SafeAgent provides the missing **trust layer** between autonomous AI systems and real engineering infrastructure.

------------------------------------------------------------------------

## Core Features

-   Autonomous file selection (LLM-guided but constrained)
-   Cryptographic file grounding (SHA-256 verification)
-   Structured patch planning
-   Patch self-repair loop (retry with improved diffs)
-   Full-file rewrite fallback for robustness
-   Policy enforcement engine
-   Diff safety validation
-   AST verification
-   Test execution enforcement
-   GitHub branch creation
-   GitHub commit automation
-   Pull Request creation
-   Automatic PR commenting (tool transparency)
-   Full execution audit logging
-   Structured execution timing trace
-   Session database with retrieval APIs
-   `/sessions`, `/sessions/{id}`, `/diff/{id}` endpoints

This is a **real agent execution platform**, not a wrapper script.

------------------------------------------------------------------------

## Design Principles

SafeAgent follows explicit engineering principles inspired by real production systems:

- **LLMs are probabilistic, infrastructure must be deterministic**
- **Trust must be earned through verification, not assumed**
- **All side effects must be auditable**
- **Failure must be safe by default**
- **Observability is a core feature, not an add-on**
- **Guardrails belong in code, not prompts**

These principles shape every architectural decision in this project.

------------------------------------------------------------------------

## Architecture Overview

SafeAgent follows principles used in high-trust production systems:

-   Immutable snapshots
-   Deterministic validation
-   Defense-in-depth
-   Sandboxed execution
-   Cryptographic grounding
-   Observability by default
-   Fail-safe behavior

You can think of it as:

> Kubernetes-style control plane for AI code agents

------------------------------------------------------------------------

## Example Workflow

``` bash
curl -X POST http://localhost:8000/run   -H "Content-Type: application/json"   -d '{
    "repo_url": "https://github.com/your/repo",
    "prompt": "Add logging to startup flow"
  }'
```

SafeAgent will:

-   Clone the repo
-   Identify relevant files
-   Propose a safe patch
-   Validate diff integrity
-   Run verification
-   Open a Pull Request
-   Leave a comment explaining what safeguards were applied
-   Store a permanent execution record

------------------------------------------------------------------------

## Observability Endpoints

SafeAgent exposes inspection APIs:

-   `GET /sessions` -- List recent executions
-   `GET /sessions/{id}` -- Full metadata, trace, plan
-   `GET /diff/{id}` -- Exact diff applied

This transforms the system from: \> "Black box agent"

into

> "Auditable autonomous system"

------------------------------------------------------------------------

### Health Check

SafeAgent exposes a standard health endpoint suitable for load balancers and uptime monitors:

- `GET /health` — Returns service status

Example:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
    "status":"ok"
}
```

This signals production readiness and operational maturity.

------------------------------------------------------------------------

## Example Execution Trace

Each run records performance timings like:

``` json
{
  "clone_ms": 842.13,
  "hash_ms": 91.42,
  "patch_ms": 1832.44,
  "repair_attempts": 1,
  "verification_ms": 642.19
}
```

This demonstrates **production maturity**, not hobby tooling.

------------------------------------------------------------------------

## Use Cases

SafeAgent is applicable to:

-   AI code review systems
-   Autonomous refactoring agents
-   Secure DevOps copilots
-   Regulated engineering environments
-   Financial infrastructure automation
-   Healthcare / compliance-sensitive pipelines
-   Enterprise agent platforms

Anywhere AI autonomy needs **guardrails and trust**.

------------------------------------------------------------------------

## Status

This repository provides a complete autonomous agent execution framework.

LLM integrations are modular and live in:

    app/llm.py

You can plug in: - OpenAI models
- Local models
- Claude
- Bedrock
- Internal enterprise LLMs

The safety infrastructure remains invariant.

------------------------------------------------------------------------

## Why This Project Exists

SafeAgent was built to explore one core question:

> What would it take to make autonomous AI coding agents trustworthy
> enough for real production systems?

This project is an attempt at answering that question with real engineering, not demos.

------------------------------------------------------------------------

## License

None

------------------------------------------------------------------------

## Author

Built by Partha Mehta as a demonstration of production-grade autonomous agent infrastructure.
