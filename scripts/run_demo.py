from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.orchestrator import AgentOrchestrator
from app.data.ingest import load_candidates_csv
from app.domain.models import ExperimentDesignSpec


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Q-Discovery Agent offline demo")
    parser.add_argument("--config", default="data/examples/demo_config.json")
    parser.add_argument("--data", default="data/examples/demo_candidates.csv")
    parser.add_argument("--output", default="artifacts/demo-result.json")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    spec = ExperimentDesignSpec.model_validate(config)
    candidates, observations = load_candidates_csv(
        args.data,
        candidate_id_column=spec.candidate_source.candidate_id_column,
        target_column=spec.candidate_source.observed_target_column,
        feature_columns=spec.candidate_source.feature_columns,
    )
    # Replay only an initial history; the remaining table rows act as the hidden oracle.
    history = observations[: max(2, len(observations) // 2)]
    result = AgentOrchestrator().run(spec, candidates, history)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "run_id": result.run_id,
        "status": result.status.value,
        "recommendations": [item.model_dump(mode="json") for item in result.recommendations],
        "verification": result.verification.model_dump(mode="json"),
        "output": str(output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
