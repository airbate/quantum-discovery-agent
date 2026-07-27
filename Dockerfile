ARG BASE_IMAGE=python:3.11-slim-bookworm@sha256:b18992999dbe963a45a8a4da40ac2b1975be1a776d939d098c647482bcad5cba
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="Q-Discovery Agent"
LABEL org.opencontainers.image.description="Self-verifying quantum-classical agent for scientific experiment batch design"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    Q_DISCOVERY_API_ALLOW_QISKIT=0

WORKDIR /opt/q-discovery-agent

# The default image is Debian Linux. A platform-specific Linux image can be
# supplied with --build-arg BASE_IMAGE=<approved-image>.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md skill.md ./
COPY app ./app

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev,quantum]"

COPY data ./data
COPY scripts ./scripts
COPY tests ./tests
COPY ui ./ui
COPY PRD.md IMPLEMENTATION-SPEC.md ./

RUN useradd --create-home --shell /usr/sbin/nologin qda \
    && mkdir -p artifacts \
    && chown -R qda:qda /opt/q-discovery-agent

USER qda

EXPOSE 8000

CMD ["python", "scripts/run_demo.py", "--output", "artifacts/linux-demo.json"]
