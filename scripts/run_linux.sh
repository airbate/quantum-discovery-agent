#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${Q_DISCOVERY_IMAGE:-q-discovery-agent:linux}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required; install Docker Engine or Docker Desktop first" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
mkdir -p artifacts

docker build --build-arg BASE_IMAGE="${Q_DISCOVERY_BASE_IMAGE:-python:3.11-slim-bookworm@sha256:b18992999dbe963a45a8a4da40ac2b1975be1a776d939d098c647482bcad5cba}" \
  -t "$IMAGE_NAME" .

docker run --rm "$IMAGE_NAME" python scripts/run_correctness.py
docker run --rm -v "$PROJECT_ROOT/artifacts:/opt/q-discovery-agent/artifacts" \
  "$IMAGE_NAME" python scripts/run_demo.py --output artifacts/linux-demo.json
docker run --rm -v "$PROJECT_ROOT/artifacts:/opt/q-discovery-agent/artifacts" \
  "$IMAGE_NAME" python scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --output artifacts/linux-benchmark.json

echo "Linux validation completed. Results are in artifacts/linux-demo.json and artifacts/linux-benchmark.json."
