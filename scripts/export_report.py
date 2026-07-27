from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a compact Markdown report from a run JSON")
    parser.add_argument("input", default="artifacts/demo-result.json", nargs="?")
    parser.add_argument("--output", default="artifacts/demo-report.md")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    verification = payload["verification"]
    lines = [
        f"# Q-Discovery Agent Run Report: {payload['run_id']}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Round: `{payload['round_id']}`",
        f"- Verification: `{verification['status']}`",
        f"- Feasible: `{verification['is_feasible']}`",
        f"- Objective: `{verification['objective_recomputed']:.6f}`",
        f"- Objective error: `{verification['objective_abs_error']:.3g}`",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in payload.get("recommendations", []):
        lines.extend(
            [
                f"### {recommendation['batch_id']}",
                "",
                f"- Candidates: {', '.join(recommendation['candidate_ids'])}",
                f"- Solver: `{recommendation['solver_kind']}`",
                f"- Predicted objective: `{recommendation['predicted_objective']:.6f}`",
                f"- Backend: `{recommendation['resource_usage']['backend']}`",
                f"- Fallback: `{recommendation['resource_usage']['fallback']}`",
                "",
            ]
        )
    lines.extend(["## Baseline comparison", ""])
    for baseline in verification.get("baseline_comparison", []):
        lines.append(
            f"- `{baseline['solver_kind']}`: value={baseline['best_value']:.6f}, "
            f"feasible={baseline['feasible']}, backend={baseline['metadata']['backend']}"
        )
    lines.extend(["", "## Agent events", ""])
    for event in payload.get("agent_events", []):
        lines.append(f"- `{event['tool_name']}` → `{event['status']}`")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
