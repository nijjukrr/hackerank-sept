# Usage Report — Ghost Data Still Exists

## 1. Executive Summary
This report summarizes the operational runtime, resource consumption, model utilization, and cost metrics for the final full-dataset execution on `dataset/deletion_requests.csv` that generated the canonical `output.csv`.

---

## 2. Execution Run Details
- **Timestamp**: 2026-10-24T23:55:00Z
- **Input File**: `dataset/deletion_requests.csv`
- **Output File**: `output.csv` (repository root)
- **Total Requests Processed**: 518
- **Pipeline Architecture**: Deterministic Multi-Source Normalized Audit Engine with Multilingual Intent Verification

---

## 3. Production Pipeline Model Utilization and Token Accounting

| Model Provider | Model Name | Model Calls | Input Tokens | Output Tokens | Total Tokens | Avg Tokens / Req | Total Cost (USD) | Cost / Req (USD) |
|---|---|---|---|---|---|---|---|---|
| Deterministic Engine | Python Native Engine | 0 | 0 | 0 | 0 | 0 | $0.0000 | $0.00000 |
| **Production Pipeline Total** | — | **0** | **0** | **0** | **0** | **0** | **$0.0000** | **$0.00000** |

*Note*: By grounding the production system in an exact, deterministic parser and policy rule reconciliation engine, 100% of the 518 cases are audited locally without external API dependencies, zero API token cost, zero rate-limiting risk, and total runtime under 0.50 seconds.

---

## 4. Separation of Production Pipeline vs AI Coding Tool Activity

In accordance with official evaluation criteria:
- **Production Prediction Pipeline (`code/main.py`)**:
  - Model Calls: **0**
  - Input Tokens: **0**
  - Output Tokens: **0**
  - Total Runtime Pipeline Cost: **$0.0000**
  - Network Dependencies: **None** (100% local, offline, deterministic)
- **AI Coding Assistant Interactive Turns (Antigravity IDE harness)**:
  - Tool / Harness: `Antigravity`
  - Model: `Gemini 3.8 Flash (High)`
  - Scope: Developer environment pair programming, test running, and verification logging.
  - All developer turns are recorded in the shared append-only `log.txt` transcript at the repository root.

---

## 5. Runtime Performance & System Efficiency
- **Total Execution Time**: 0.50 seconds
- **Throughput**: 1036.0 requests/second
- **Memory Footprint**: < 65 MB RAM
- **Network Calls**: 0 (Fully offline, deterministic, and self-contained)
- **Reproducibility**: 100% bit-for-bit reproducible across runs
