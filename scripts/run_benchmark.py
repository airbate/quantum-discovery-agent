from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.ingest import load_candidates_csv
from app.domain.models import ExperimentDesignSpec


def main() -> None:
    parser = argparse.ArgumentParser(description="Run seeded baseline/QAOA comparison")
    parser.add_argument("--config", default="data/examples/demo_config.json")
    parser.add_argument("--data", default="data/examples/demo_candidates.csv")
    parser.add_argument("--seeds", default="1,2,3,4,5")
    parser.add_argument("--output", default="artifacts/benchmark.json")
    args = parser.parse_args()
    spec_payload = json.loads(Path(args.config).read_text(encoding="utf-8"))
    candidates, observations = load_candidates_csv(
        args.data,
        candidate_id_column=spec_payload["candidate_source"]["candidate_id_column"],
        target_column=spec_payload["candidate_source"]["observed_target_column"],
        feature_columns=spec_payload["candidate_source"]["feature_columns"],
    )
    history = observations[: max(2, len(observations) // 2)]
    records = []
    for raw_seed in args.seeds.split(","):
        seed = int(raw_seed)
        payload = dict(spec_payload)
        payload["run_id"] = f"benchmark-{seed}"
        payload["solver"] = dict(payload["solver"])
        payload["solver"]["seed"] = seed
        spec = ExperimentDesignSpec.model_validate(payload)
        result = __import__("app.service", fromlist=["ExperimentService"]).ExperimentService().run_round(spec, candidates, history)
        records.append({
            "seed": seed,
            "status": result.status.value,
            "verification": result.verification.model_dump(mode="json"),
            "baselines": [item.model_dump(mode="json") for item in result.verification.baseline_comparison],
        })
    summary = {
        "runs": records,
        "seed_count": len(records),
        "feasible_rates": [item["verification"]["stability"]["feasible_rate"] for item in records],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "seed_count": len(records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
