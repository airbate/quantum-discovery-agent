#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_ROOT/artifacts/single-card-evidence}"

if [[ -n "${Q_DISCOVERY_PYTHON:-}" ]]; then
  PYTHON_BIN="$Q_DISCOVERY_PYTHON"
elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "Python 3.10 or newer is required" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_ROOT"

SUPA_ENV="/usr/local/birensupa/sdk/1.11.0.0.rc2/scripts/brsw_set_env.sh"
if [[ -f "$SUPA_ENV" ]]; then
  # shellcheck disable=SC1091
  source "$SUPA_ENV" >/dev/null
fi

QUBO_DEVICE="${Q_DISCOVERY_QUBO_DEVICE:-}"
if [[ -z "$QUBO_DEVICE" ]]; then
  if command -v brsmi >/dev/null 2>&1 || command -v br-smi >/dev/null 2>&1; then
    QUBO_DEVICE="supa"
  else
    QUBO_DEVICE="cpu"
  fi
fi

run_and_log() {
  local name="$1"
  shift
  {
    printf '$'
    printf ' %s' "$@"
    printf '\n'
    "$@"
  } 2>&1 | tee "$OUTPUT_DIR/$name.log"
}

{
  printf 'collected_at_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'project_root=%s\n' "$PROJECT_ROOT"
  printf 'git_commit=%s\n' "$(git rev-parse HEAD 2>/dev/null || printf unknown)"
  printf 'uname=%s\n' "$(uname -a)"
  printf 'python=%s\n' "$($PYTHON_BIN --version 2>&1)"
  if [[ -f /etc/os-release ]]; then
    printf '\n[os-release]\n'
    cat /etc/os-release
  fi
  if command -v lscpu >/dev/null 2>&1; then
    printf '\n[lscpu]\n'
    lscpu
  fi
  printf '\n[python-packages]\n'
  "$PYTHON_BIN" -m pip show torch torch_br UnitaryLab unitarylab-algorithms \
    qiskit qiskit-aer fastapi pydantic 2>/dev/null || true
  printf '\n[runtime-smoke-check]\n'
  "$PYTHON_BIN" - <<'PY'
import importlib.metadata
import torch
import torch_br
import unitarylab

print("torch", torch.__version__)
print("torch_br", torch_br.__file__)
print("UnitaryLab", importlib.metadata.version("UnitaryLab"), unitarylab.__file__)
print("supa_device_count", torch.supa.device_count())
PY
} > "$OUTPUT_DIR/environment.log" 2>&1

{
  detected=0
  for tool in br-smi brsmi nvidia-smi rocm-smi amd-smi xpu-smi; do
    if command -v "$tool" >/dev/null 2>&1; then
      detected=1
      printf '\n[%s]\n' "$tool"
      "$tool" 2>&1 || true
    fi
  done
  if [[ "$detected" -eq 0 ]]; then
    printf 'No supported accelerator inventory command was found.\n'
  fi
  printf '\n[visible-device-environment]\n'
  for variable in CUDA_VISIBLE_DEVICES HIP_VISIBLE_DEVICES ROCR_VISIBLE_DEVICES \
    ONEAPI_DEVICE_SELECTOR BIREN_VISIBLE_DEVICES; do
    if [[ -n "${!variable:-}" ]]; then
      printf '%s=%s\n' "$variable" "${!variable}"
    fi
  done
} > "$OUTPUT_DIR/accelerator.log" 2>&1

run_and_log pytest "$PYTHON_BIN" -m pytest
run_and_log correctness "$PYTHON_BIN" scripts/run_correctness.py
run_and_log demo "$PYTHON_BIN" scripts/run_demo.py --qubo-device "$QUBO_DEVICE" \
  --output "$OUTPUT_DIR/demo-result.json"
run_and_log benchmark "$PYTHON_BIN" scripts/run_benchmark.py --seeds 1,2,3,4,5 \
  --qubo-device "$QUBO_DEVICE" \
  --output "$OUTPUT_DIR/benchmark-result.json"
run_and_log supa-correctness "$PYTHON_BIN" scripts/run_supa_correctness.py \
  --device "$QUBO_DEVICE" --output "$OUTPUT_DIR/supa-correctness.json"

cat > "$OUTPUT_DIR/README.txt" <<'EOF'
This directory is raw platform evidence. Before submission, confirm that:
1. accelerator.log identifies exactly the intended single card;
2. environment.log records the actual host/container and git commit;
3. demo/benchmark logs agree with the JSON result files;
4. the report states whether the accelerator participated in core computation.
Do not describe device visibility as GPU acceleration unless the backend log proves it.
EOF

(
  cd "$OUTPUT_DIR"
  if command -v sha256sum >/dev/null 2>&1; then
    find . -maxdepth 1 -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
  else
    find . -maxdepth 1 -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS.txt
  fi
)

printf 'Evidence collected in %s\n' "$OUTPUT_DIR"
